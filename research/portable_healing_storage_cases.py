"""Shared authored storage programs; no CPU-produced runtime state."""
import copy
from portable_stun_cases import fixtures as status_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(status_fixtures()[0])
    base.update(duration=.8,effects=[],owners=[],state_queries=[],observe_healing_storage=True)
    base['patterns']=[dict(id='incoming',kind='attack',delay=.15,spec=dict(atk=1300,coeff=100,target='all',hits=3,interval=.2,pierce=True))]
    def store(value=20,target='self',name='storage',**kw):return field('heal_overcharge_store',value,target,name,**kw)
    def heal(value=40,target='self',name='heal',timing='battle_start'):return instant('heal_hp_pct',value,target,name,timing)
    def drain(value=50,target='self',name='drain',timing='battle_start'):return instant('current_hp_reduce',value,target,name,timing)
    rows=[]
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='healing-storage-'+name,effects=effects,owners=owners or [0]*len(effects));rows.append(c);return c
    add('unfilled',[store()])
    add('excess-fills-and-body-spends',[store(),heal()])
    add('body-healing-before-excess',[drain(),store(),heal()])
    add('zero-capacity',[store(0),heal()])
    add('negative-capacity',[store(-20),heal()])
    add('negative-heal-does-not-fill',[store(),heal(-20)])
    add('all-allies',[store(target='all_allies'),heal(target='all_allies')])
    c=add('caster-capacity',[store(target=roster_names(base)[0]),heal()],[1,0]);c['environment']['allies'][1]['base_hp']=20000
    add('outgoing-and-received',[field('outgoing_heal_pct',50,'self','outgoing'),field('heal_received_pct',50,'self','received'),store(80),heal(20)])
    add('lifesteal-fills',[store(),field('lifesteal_pct',100,'self','lifesteal')])
    add('drain-spends-first',[store(),heal(),drain()])
    add('negative-drain-does-not-spend',[store(),heal(),drain(-50)])
    add('finite-expiry',[store(duration=.2),heal()])
    add('refresh-preserves-quantity',[store(timing='every:0.2s'),heal(timing='on_attack_count:3')])
    c=add('exact-expiry-reapplication',[store(duration=.2),heal()]);c['effects'][0]['trigger']['timing']=['battle_start','every:0.2s']
    add('same-time-stable-overlap',[store(name='first'),store(30,name='second'),heal()])
    add('newest-activation-first',[store(name='first'),store(30,name='second',timing='every:0.1s'),heal(timing='on_attack_count:3')])
    remove=instant('remove_named_buff',1,'self','remove','on_attack_count:2');remove['target_effect']='storage'
    add('named-removal',[store(),heal(),remove])
    add('capacity-before-maxhp',[store(),field('max_hp_pct',100,'self','hp'),heal()])
    add('capacity-after-maxhp',[field('max_hp_pct',100,'self','hp'),store(),heal()])
    c=add('stacked-refresh',[store(max_stack=3),heal()]);c['effects'][0]['trigger']['timing']=['battle_start','every:0.2s']
    add('lazy-ranked-recipient',[store(target='allies_top_atk:1'),heal(target='all_allies')])
    add('conditional-capacity',[store(condition=['self_hp_above:75']),heal(),drain()])
    add('shield-and-decoy-before-storage',[store(),heal(),field('shield_from_max_hp_pct',10,'self','shield'),field('decoy',10,'self','decoy')])
    add('undying-after-storage',[store(),heal(),field('undying',1,'self','undying')])
    add('invincibility-does-not-spend',[store(),heal(),field('invincible',1,'self','invincible')])
    add('cover-repair-does-not-fill',[store(),instant('cover_heal_pct',100,'self','repair')])
    add('negative-drain-without-storage',[drain(-50)])
    add('negative-drain-with-finite-hp-sync',[field('max_hp_pct',10,'self','finite-hp',duration=.2),store(),heal(),drain(-50)])
    add('overmax-before-store-and-heal',[drain(-50),store(),heal(10)])
    add('lazy-storage-with-lifesteal',[store(target='allies_top_atk:1'),field('lifesteal_pct',100,'all_allies','lifesteal')])
    add('maxhp-grant-does-not-fill',[store(),field('max_hp_pct',100,'self','hp')])
    for label,condition in [('ordinary',[]),('defender',['has_defender_ally']),('no-defender',['no_defender_ally'])]:
        periodic=heal(10,target='all_allies');periodic.update(duration=.4,tick_interval=.1)
        periodic['trigger']['condition']=condition
        add('periodic-'+label,[store(target='all_allies'),periodic])
    periodic=heal(10,timing='every:0.2s');periodic.update(duration=.3,tick_interval=.1)
    add('periodic-refresh',[store(),periodic])
    for label,target,limit in [('one-all','all_allies',1),('all-all','all_allies',0),('one-self','self',1)]:
        add('cleanse-'+label,[store(target='all_allies'),heal(target='all_allies'),
            field('atk_pct',-20,'all_allies','harmful-first',polarity='harmful'),
            field('atk_pct',-30,'all_allies','harmful-second',polarity='harmful'),
            instant('debuff_cleanse',limit,target,'cleanse')])
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(fixtures()[1])[0];row=L['DEFINITION_BASE']
    rows=[]
    for name,at,value in [('missing-policy',L['PROTECTION_DEFINITION_BASE'],0),
                          ('wrong-kind',row+F['KIND'],4),('no-combat',3,0),
                          ('nan',row+F['VALUE']+1,0x7ff80000),
                          ('invalid-policy',L['PROTECTION_DEFINITION_BASE'],10),
                          ('invalid-hp-policy',L['HP_UNCLAMP_POLICY'],2),
                          ('unjustified-hp-policy',L['HP_UNCLAMP_POLICY'],1)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/healing-storage-'+name,raw,None))
    raw=list(seed);raw[L['PROTECTION_DEFINITION_BASE']]=0;raw[L['PROTECTION_META_BASE']]=0
    rows.append(('reject/healing-storage-missing-policy-and-meta',raw,None))
    periodic=next(c for c in fixtures() if c['name']=='healing-storage-periodic-defender')
    seed=compile_case(periodic)[0];condition=L['CONDITION_BASE']+L['CONDITION_WORDS']
    for label,at,value in [('static-name',condition+1,1),('static-two',condition+3,0x40000000)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/healing-storage-'+label,raw,None))
    cleanse=next(c for c in fixtures() if c['name']=='healing-storage-cleanse-one-all')
    seed=compile_case(cleanse)[0];row=L['DEFINITION_BASE']+4*L['DEFINITION_WORDS']
    for label,at,value in [('cleanse-nan',row+F['VALUE']+1,0x7ff80000),('cleanse-scope',row+F['TARGET'],0)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/healing-storage-'+label,raw,None))
    return rows
