"""Canonical79: additive named caster-ATK magnitude, one native/CUDA/Metal table."""
import copy
from portable_persona_cases import fixtures as persona_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(persona_fixtures()[0]);base.update(effects=[],owners=[],duration=.8,base_atk=[1000,2000,1500,900,800])
    names=roster_names(base);rows=[]
    def grant(value=20,target='all_allies',name='grant',**kw):return field('atk_caster_based_pct',value,target,name,**kw)
    def amp(value=50,target='all_allies',ref='grant',name='magnitude',**kw):return field('atk_buff_mag_pct',value,target,name,target_effect=ref,**kw)
    def add(label,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='attack-mag-'+label,effects=effects,owners=owners if owners is not None else [0]*len(effects));rows.append(c);return c
    add('baseline',[grant()])
    for value in (0,50,-50,-100,-150):add('value-'+str(value),[grant(),amp(value)])
    add('wrong-name',[grant(),amp(ref='unrelated')])
    add('other-owner-applies',[grant(),amp()],[0,1])
    add('one-recipient',[grant(),amp(target=names[1])])
    add('other-recipient',[grant(target=names[0]),amp(target=names[1])])
    add('only-atk-caster',[field('atk_pct',20,'all_allies','grant'),amp()])
    add('only-atk-caster-hp',[field('atk_from_hp_pct',20,'all_allies','grant'),amp()])
    add('only-atk-caster-copy',[field('atk_copy',20,'all_allies','grant',copy_from='allies_top_atk:1'),amp()])
    add('unrelated-base-keeps-contribution',[grant(),grant(30,name='other'),amp()])
    add('multiple-owners-same-name',[grant(),grant(30),amp()],[0,1,2])
    add('two-additive',[grant(),amp(50,name='one'),amp(25,name='two')])
    add('ordered-cancellation',[grant(),amp(1e16,name='one'),amp(-1e16,name='two'),amp(1,name='three')])
    add('reverse-ordered-cancellation',[grant(),amp(1,name='three'),amp(-1e16,name='two'),amp(1e16,name='one')])
    add('runtime-false-still-applies',[grant(),amp(timing='passive',condition=['self_hp_below:10'])])
    add('finite-false-no-carrier',[grant(),amp(duration=.4,condition=['self_hp_below:10'])])
    add('base-runtime-false',[grant(timing='passive',condition=['self_hp_below:10']),amp()])
    add('expiry',[grant(),amp(duration=.4)])
    add('base-expiry',[grant(duration=.4),amp()])
    add('stacked',[grant(max_stack=3,timing='on_attack'),amp(max_stack=3,timing='on_attack')])
    add('gear',[grant(),dict(amp(),_source_tag='equipment')])
    add('scaling-reference',[grant(),field('atk_pct',0,'self','reference',timing='on_attack',max_stack=3),amp(scaling='stack_count',scaling_ref='reference')])
    add('base-scaling-reference',[field('atk_pct',0,'self','reference',timing='on_attack',max_stack=3),grant(scaling='stack_count',scaling_ref='reference'),amp()])
    add('lazy-fresh-rank',[grant(),amp(target='allies_top_atk:1'),field('atk_pct',500,names[0],'reverse',timing='every:0.4s')])
    add('lazy-shared-with-mapped-sibling',[grant(),amp(target='allies_top_atk:1'),field('crit_dmg',10,'allies_top_atk:1','sibling'),field('atk_pct',500,names[0],'reverse',timing='every:0.4s')])
    add('rank-does-not-use-magnitude',[grant(target=names[0]),amp(target=names[0],value=10000),field('crit_dmg',20,'allies_top_atk:1','rank-witness',timing='every:0.2s')])
    add('base-lazy',[grant(target='allies_top_atk:1'),amp(),field('atk_pct',500,names[0],'reverse',timing='every:0.4s')])
    c=add('base-lazy-incoming-freezes-before-rank-reversal',[grant(target='allies_top_atk:1'),amp(),field('atk_pct',500,names[0],'reverse',timing='every:0.4s')]);c['patterns']=[dict(id='idle',kind='idle'),dict(id='incoming',kind='attack',delay=.3,spec=dict(atk=10,coeff=100,target='all',hits=1))]
    add('lazy-runtime-false-still-applies',[grant(),amp(target='allies_top_atk:1',timing='passive',condition=['self_hp_below:10'])])
    add('mixed-late-hp-and-copy',[field('atk_copy',20,'all_allies','copied',copy_from='allies_top_atk:1'),field('atk_from_hp_pct',1,'all_allies','hp'),grant(),amp()])
    c=add('amplifier-owner-down',[grant(),amp()],[0,1]);c['patterns']=[dict(id='idle',kind='idle'),dict(id='down',kind='attack',delay=.3,spec=dict(atk=1e8,coeff=100,target='slot:2',hits=1))]
    add('named-child',[grant(),amp(),dict(name='child',source='스킬1',type='damage',stat='damage',fixed_value=100,target='target',trigger=dict(timing=['event:magnitude'],condition=[]))])
    add('removed',[grant(),amp(),dict(instant('remove_named_buff',1,'self','remove','every:0.3s'),target_effect='magnitude')])
    add('base-removed',[grant(),amp(),dict(instant('remove_named_buff',1,'self','remove','every:0.3s'),target_effect='grant')])
    add('alias-same-name',[grant(),amp(),amp(25,timing='every:0.2s')])
    c=add('enemy-amplifier-does-not-affect-allies',[grant(),amp(target='all_enemies')]);c['patterns']=[dict(id='idle',kind='idle'),dict(id='wave',kind='summon',spec=dict(count=2,hp=1e15))]
    c=add('enemy-attack-not-amplified',[grant(target='all_enemies',value=-10),amp(target='all_enemies')]);c['patterns']=[dict(id='incoming',kind='attack',delay=.2,spec=dict(atk=300,coeff=100,target='all',hits=2,interval=.2))]
    from world_pending_cases import fixtures as pending_fixtures
    c=copy.deepcopy(pending_fixtures()[0]);c['name']='attack-mag-pending'
    for key,value in base.items():
        if key not in c:c[key]=copy.deepcopy(value)
    c['effects'] += [grant(target='all_allies'),amp()];c['owners'] += [0,1]
    c.update(observe_named_state=True,observe_enemy_fields=True,observe_counter_field_memberships=True);rows.append(c)
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(next(c for c in fixtures() if c['name']=='attack-mag-value-50'))[0];d=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];extra=L['DEFINITION_EXTRA_BASE']+L['DEFINITION_EXTRA_WORDS']
    rows=[]
    for label,at,value in [('kind',d+F['KIND'],4),('missing-reference',d+F['TARGET_NAME'],0xffffffff),('reference-overflow',d+F['TARGET_NAME'],L['DEFINITIONS']),('nan',d+F['VALUE']+1,0x7ff80000),('infinity',d+F['VALUE']+1,0x7ff00000),('unknown-stat',d+F['STAT'],0xffffffff),('persona',extra+3,1),('query-resolve',L['RECIPIENT_BASE']+8+7,5),('health',L['HEALTH_DEFINITION_BASE']+L['HEALTH_DEFINITION_WORDS']+1,1),('no-combat',3,0)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/attack-mag-'+label,raw,None))
    return rows
