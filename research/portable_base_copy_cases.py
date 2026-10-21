"""Literal full battles for base-copy activation, lifetime and child ordering."""
import copy
from portable_stun_cases import fixtures as status_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    base=copy.deepcopy(status_fixtures()[0]);base.update(effects=[],owners=[],duration=.8,
        observe_base_copies=True,base_atk=[1000,2000,1500,900,800],patterns=[dict(id='idle',kind='idle')])
    for ally,hp in zip(base['environment']['allies'],(1000,2000,1500,900,800)):ally.update(base_hp=hp,hp=hp)
    for w in base['combat']['weapons']:w.update(interval=.2,capacity=1000)
    from world_frame_native import roster_names
    names=roster_names(base)
    rows=[]
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='base-copy-'+name,effects=effects,owners=owners if owners is not None else [0]*len(effects));rows.append(c);return c
    def copied(stat='hp_copy',value=50,**kw):
        return field(stat,value,'self','copied',copy_from='allies_top_hp:1' if stat=='hp_copy' else 'allies_top_atk:1',**kw)
    for stat in ('atk_copy','hp_copy'):
        for value in (0,20,50,-10):add(stat+'-'+str(value),[copied(stat,value)])
        add(stat+'-reverse-final-rank',[field('atk_pct' if stat=='atk_copy' else 'max_hp_only_pct',200,names[2],'reverse'),copied(stat)])
        add(stat+'-expire',[copied(stat,duration=.3)])
        add(stat+'-refresh',[copied(stat,timing='on_attack',duration=.3)])
        add(stat+'-stacked',[copied(stat,timing='on_attack',duration=.3,max_stack=3)])
        c=add(stat+'-tie',[copied(stat)]);c['base_atk'][0]=2000;c['environment']['allies'][0].update(base_hp=2000,hp=2000)
        c=add(stat+'-allies',[dict(copied(stat),target='all_allies')])
        add(stat+'-initial-stacks',[copied(stat,timing='on_attack_count:3',max_stack=5),dict(instant('buff_stack_init',2,'self','initial'),target_effect='copied')])
    add('no-refresh-heal',[copied(timing='on_attack'),instant('current_hp_reduce',50,'self','loss','on_attack_count:2')])
    add('gift-is-not-healing',[field('heal_received_pct',999,'self','heal'),copied()])
    add('child-damage-sees-basis',[copied('atk_copy'),dict(name='child',source='스킬1',type='damage',stat='bonus_damage',fixed_value=100,target='same_target',trigger=dict(timing=['event:copied'],condition=[]))])
    add('removed-parent',[copied(),dict(instant('remove_named_buff',0,'self','remove','event:copied'),target_effect='copied')])
    add('removed-recipient',[dict(copied(),target='all_allies'),dict(instant('remove_named_buff',0,'self','remove','event:copied'),target_effect='copied',remove_scope='target')])
    add('removed-parent-reinstalled',[instant('current_hp_reduce',50,'self','initial-loss'),copied(timing='on_attack',max_stack=5),dict(instant('remove_named_buff',0,'self','remove','event:copied'),target_effect='copied',max_trigger=1),dict(instant('buff_stack_init',1,'self','reinstall','event:copied'),target_effect='copied',max_trigger=1)])
    add('negative-with-positive-expiry',[dict(copied(value=-10),name='negative'),dict(copied(duration=.3),name='temporary')])
    add('negative-expiry-child',[dict(copied(value=-10),name='negative'),dict(copied(duration=.3),name='temporary'),instant('heal_hp_pct',10,'self','end-heal','event:state_end:temporary')])
    for stat in ('atk_copy','hp_copy'):
        c=add(stat+'-source-down-refresh',[copied(stat,timing='on_attack')])
        c['patterns']=[dict(id='kill-source',kind='attack',delay=.25,spec=dict(atk=10000000,coeff=100,target='slot:2',hits=1))]
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    from portable_base_copy_specs import OFFSET,FLAG
    seed=compile_case(next(c for c in fixtures() if c['name']=='base-copy-hp_copy-50'))[0];d=L['DEFINITION_BASE'];meta=L['MODE_BASE']+OFFSET
    edits=[('no-combat',3,0),('kind',d+F['KIND'],4),('stat',d+F['STAT'],99),('nan',d+F['VALUE']+1,0x7ff80000),
        ('magic',meta,0),('axis',meta+2,1),('identity',meta+1,85),('unused',meta+3,1),('tail',meta+4,1),
        ('missing-tag',L['DEFINITION_EXTRA_BASE']+3,0),('mixed-tag',L['DEFINITION_EXTRA_BASE']+3,FLAG|512),
        ('bullet',L['BULLET_DEFINITION_BASE'],2),('enemy',L['HEALTH_DEFINITION_BASE']+3,1),('bad-hp-policy',L['HP_UNCLAMP_POLICY'],2)]
    rows=[]
    for label,at,value in edits:
        raw=list(seed);raw[at]=value;rows.append(('reject/base-copy-'+label,raw,None))
    unjustified=compile_case(fixtures()[1])[0];unjustified[L['HP_UNCLAMP_POLICY']]=1
    rows.append(('reject/base-copy-unjustified-hp-policy',unjustified,None))
    return rows
