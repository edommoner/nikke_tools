"""Stun presence, immunity and activation predicates; one CUDA/Metal input set."""
import copy
from portable_recipient_extension_cases import fixtures as recipient_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(recipient_fixtures()[0]);base.update(duration=.8,effects=[],owners=[],state_queries=[])
    rows=[]
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='stun-'+name,effects=effects,owners=owners or [0]*len(effects));rows.append(c);return c
    def stun(target='self',duration=-1,value=1,**kw):return field('stun',value,target,'stun',duration=duration,**kw)
    def immune(target='self',duration=-1,value=0,**kw):return field('stun_immune',value,target,'immune',duration=duration,**kw)
    def witness(condition='target_stunned'):
        return dict(name='witness',source='스킬1',type='damage',stat='bonus_damage',fixed_value=100,
            target='same_target',trigger=dict(timing=['on_attack'],condition=[condition]))
    add('baseline',[field('atk_pct',0,'self','baseline')])
    for value in (0,1,-3):add('self-presence-'+str(value),[stun(value=value)])
    add('self-finite',[stun(duration=.3)])
    add('ally-immunity-after',[stun(),immune()])
    add('ally-immunity-before',[immune(),stun()])
    add('ally-immunity-expires',[stun(),immune(duration=.3)])
    add('allies',[stun('all_allies',duration=.3)])
    add('ranked-ally',[stun('allies_top_atk:1')])
    add('ranked-immune',[stun('all_allies'),immune('allies_top_atk:1')])
    add('predicate-without-status',[witness()])
    for target in ('boss','target','all_enemies','enemies_lowest_hp:1'):
        add('enemy-'+target,[stun(target,duration=.3),witness()])
    add('enemy-immune-after',[stun('boss'),immune('boss'),witness()])
    add('enemy-immune-before',[immune('boss'),stun('boss'),witness()])
    add('enemy-immune-expires',[stun('boss'),immune('boss',duration=.3),witness()])
    add('immune-predicate',[immune(),witness('self_stun_immune')])
    add('immune-predicate-expires',[immune(duration=.3),witness('self_stun_immune')])
    add('immune-predicate-from-other-owner',[immune(roster_names(base)[0]),witness('self_stun_immune')],[1,0])
    for target in ('boss','all_enemies','enemies_lowest_hp:1'):
        c=add('body-predicate-with-add-'+target,[stun(target),witness()])
        c['patterns']=[dict(id='adds',kind='summon',spec=dict(count=2,hp=1e8,atk=1))]
    add('debuff-immunity',[field('debuff_immune',0,'self','harmful-immune'),stun(polarity='harmful')])
    add('remove-enemy-state',[stun('boss'),witness(),
        dict(instant('remove_named_buff',1,'boss','remove','on_attack_count:2'),target_effect='stun')])
    c=add('burst-selection',[instant('burst_charge_pct',100,'all_allies','initial-gauge'),stun(duration=.3)])
    for i,w in enumerate(c['combat']['weapons']):w['stage']=[1,1,2,3,3][i]
    c=add('charge-waits-through-stun',[stun(duration=.3)])
    c['combat']['weapons'][0].update(mode='charge',base_weapon_type='SR',charge=.2,interval=.4,min_cycle=.2,full_charge_mult=300,gauge_mult=100)
    c['post_fire_delays'][0]=.2
    c=add('burst-all-candidates-stunned',[instant('burst_charge_pct',100,'all_allies','initial-gauge'),stun('all_allies',duration=.3)])
    for i,w in enumerate(c['combat']['weapons']):w['stage']=[1,1,2,3,3][i]
    c=add('late-add-not-retargeted',[stun('all_enemies'),witness()])
    c['patterns']=[dict(id='late-add',kind='summon',delay=.3,spec=dict(count=1,hp=1e8,atk=1))]
    c=copy.deepcopy(rows[28]);c['name']='stun-manual-charge-keeps-arbitration';c['weapon_metadata']=dict(input_type='UP');c['controls']=[{} for _ in range(5)];c['controls'][0]=dict(sequence=[dict(action='hold',t=0,until=.6)]);rows.append(c)
    add('shot-child-finishes-current-packet',[stun(timing='on_attack',max_trigger=1)])
    c=copy.deepcopy(rows[28]);c['name']='stun-interrupts-existing-charge';c['effects'][0]['trigger']['timing']=['every:0.1s'];c['effects'][0]['max_trigger']=1;c['effects'][0]['duration']=.15;rows.append(c)
    c=add('reopened-add-generation',[stun('all_enemies'),witness()])
    c['patterns']=[dict(id='wave',kind='summon',after=['start','wave'],until=dict(time=.1),repeat=0,spec=dict(count=1,hp=1e8,atk=1))]
    c=add('wide-128-recipients',[stun('all_enemies'),witness()])
    c['patterns']=[dict(id='wide',kind='summon',spec=dict(count=127,hp=1e8,atk=1))]
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(fixtures()[2])[0];d=L['DEFINITION_BASE']
    rows=[]
    for label,at,value in [('no-combat',3,0),('kind',d+F['KIND'],4),('zero-presence',d+F['VALUE']+1,0),('nan-presence',d+F['VALUE']+1,0x7ff80000)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/stun-'+label,raw,None))
    seed=compile_case(fixtures()[19])[0];at=L['DEFINITION_EXTRA_BASE']+3
    raw=list(seed);raw[at]=3;rows.append(('reject/stun-immune-flags',raw,None))
    raw=list(seed);raw[d+F['KIND']]=0;rows.append(('reject/stun-immune-kind',raw,None))
    for label,slot in [('target',11),('immune',19)]:
        seed=compile_case(fixtures()[slot])[0];at=L['CONDITION_BASE']+(0 if slot==11 else 1)*L['CONDITION_WORDS']
        for word in (1,2):
            raw=list(seed);raw[at+word]=1;rows.append((f'reject/{label}-predicate-word{word}',raw,None))
    return rows
