"""Literal live lost-HP attack contracts; no packing or GPU expected data."""
import copy
from portable_skill_hp_basis_cases import fixtures as hp_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field

def fixtures():
    base=copy.deepcopy(hp_fixtures()[0]);base.update(effects=[],owners=[],duration=.25)
    base['enemy']['def']=0
    for target in base['combat']['targets']:target['defense']=0
    rows=[]
    def add(label,*,value=1,drain=50,packets=(1500,),rates=(50,),hp_rates=(50,),owner=0):
        c=copy.deepcopy(base);c['name']='lost-hp-attack-'+label
        attack=field('atk_pct',value,'self','lost-attack',scaling='lost_hp_pct')
        hit=dict(name='parts-source',source='skill2',type='damage',stat='damage',fixed_value=100,target='target',trigger=dict(timing=['battle_start'],condition=[]))
        c['effects']=[attack,field('crit_rate',-100,'self','no-crit')]
        if drain is not None:c['effects'].append(instant('current_hp_reduce',drain,'self','initial-drain'))
        c['effects'].append(hit);c['owners']=[owner]*len(c['effects'])
        c['contract']=dict(owner=owner,damage=[sum(packets) if i==owner else 0 for i in range(5)],packets=list(packets),rates=list(rates),hp_rates=list(hp_rates))
        rows.append(c);return c
    add('half')
    add('full',drain=0,packets=[1000],rates=[0],hp_rates=[100])
    add('quarter-lost',drain=25,packets=[1250],rates=[25],hp_rates=[75])
    add('zero-current-hp',drain=100,packets=[2000],rates=[100],hp_rates=[0])
    add('above-maximum',drain=-20,packets=[1000],rates=[0],hp_rates=[120])
    add('negative',value=-.5,packets=[750],rates=[-25])
    add('fractional-ties-even',value=.125,packets=[1062],rates=[6.25])
    add('more-than-100-percent',value=2,drain=75,packets=[2500],rates=[150],hp_rates=[25])
    add('last-owner',owner=4)
    c=add('stack-count-ignored',packets=[1500]*3,rates=[50]*3,hp_rates=[50]*3);c['duration']=.35
    c['effects'][0].update(max_stack=3);c['effects'][0]['trigger']['timing']=['battle_start','every:0.1s'];c['effects'][-1]['trigger']['timing']=['every:0.1s'];c['contract']['max_observed_stack']=3
    c=add('finite-expiry',packets=[1500,1000],rates=[50,0],hp_rates=[50,50]);c['effects'][0]['duration']=.15;c['effects'][-1]['trigger']['timing']=['every:0.1s']
    c=add('two-contributions',value=.125,packets=[1250],rates=[25]);c['effects'].insert(1,field('atk_pct',.375,'self','lost-attack-2',scaling='lost_hp_pct'));c['owners'].insert(1,0)
    c=add('drain-between-activations',drain=None,packets=[1000,1500,1750],rates=[0,50,75],hp_rates=[100,50,25]);c['duration']=.35;c['effects'][-1]['trigger']['timing']=['every:0.1s']
    c['effects'].insert(-1,instant('current_hp_reduce',50,'self','hit-drain','hit_count:parts-source:1'));c['owners'].insert(-1,0)
    c=add('heal-between-activations',drain=75,packets=[1750,1500,1250],rates=[75,50,25],hp_rates=[25,50,75]);c['duration']=.35;c['effects'][-1]['trigger']['timing']=['every:0.1s']
    c['effects'].insert(-1,instant('heal_hp_pct',25,'self','hit-heal','hit_count:parts-source:1'));c['owners'].insert(-1,0)
    c=add('maximum-hp-changes-rate',packets=[1750],rates=[75],hp_rates=[25]);c['effects'].insert(-1,field('max_hp_only_pct',100,'self','double-maximum'));c['owners'].insert(-1,0)
    c=add('incoming-without-health-buff',drain=None,packets=[1100,1200],rates=[10,20],hp_rates=[90,80]);c['effects'][-1]['trigger']['timing']=['every:0.1s']
    c['patterns']=[dict(id='injury',kind='attack',delay=.05,spec=dict(atk=1000,coeff=100,target='slot:1',hits=2,interval=.1,pierce=True))]
    c=add('shield-is-not-hp-loss',packets=[1500,1500],rates=[50,50],hp_rates=[50,50]);c['effects'][-1]['trigger']['timing']=['every:0.1s']
    c['effects'].insert(0,field('shield_from_max_hp_pct',10,'self','shield'));c['owners'].insert(0,0);c['patterns']=[dict(id='blocked',kind='attack',delay=.05,spec=dict(atk=500,coeff=100,target='slot:1',hits=1))]
    c=add('runtime-predicate',packets=[1500,1000],rates=[50,0],hp_rates=[50,100]);c['effects'][0]['trigger']['condition']=['self_hp_below:75'];c['effects'][-1]['trigger']['timing']=['every:0.1s']
    c['effects'].insert(-1,dict(instant('heal_hp_pct',50,'self','once-heal','hit_count:parts-source:1'),max_trigger=1));c['owners'].insert(-1,0)
    absent=copy.deepcopy(c);absent['name']='lost-hp-attack-initial-predicate-false';absent['contract'].update(damage=[2000,0,0,0,0],packets=[1000,1000],rates=[0,0],scalar_absent=True);rows.append(absent)
    # Infinite runtime predicates must also pass activation before later queries.
    c['effects'].insert(0,c['effects'].pop(2))
    c=add('parent-snapshot-and-child-refresh',packets=[1500,1500],rates=[50,25,0],hp_rates=[50,75,100]);c['effects'][-1]['stat']='sequential_damage:2';c['contract']['damage'][0]=5250
    child=dict(name='lost-child',source='nested',type='damage',stat='damage',fixed_value=100,target='target',trigger=dict(timing=['hit_count:parts-source:1'],condition=[]))
    c['effects'][-1:-1]=[instant('heal_hp_pct',25,'self','child-heal','hit_count:parts-source:1'),child];c['owners'][-1:-1]=[0,0]
    c=add('physical-live-hp',packets=[],rates=[],hp_rates=[]);c['effects'].pop();c['owners'].pop();c['contract']['damage'][0]=4800;c['contract']['physical_packets']=[1500,1600,1700]
    c['combat']['weapons'][0].update(mode='auto',interval=.1,pellets=1,muzzles=1,capacity=5)
    c['patterns']=[dict(id='injury',kind='attack',delay=.05,spec=dict(atk=1000,coeff=100,target='slot:1',hits=2,interval=.1,pierce=True))]
    scalar_extras={'two-contributions':[6.25,18.75],'drain-between-activations':[0,50,75,87.5],'heal-between-activations':[0,25,50,75],'incoming-without-health-buff':[0,10,20],'physical-live-hp':[50,60,70]}
    for c in rows:
        label=c['name'].removeprefix('lost-hp-attack-');c['contract']['scalar_values']=scalar_extras.get(label,list(c['contract']['rates']))
        c['contract']['sample_names']=['parts-source']*len(c['contract']['rates'])
        if label=='parent-snapshot-and-child-refresh':c['contract']['sample_names']=['parts-source','lost-child','lost-child']
    return rows
