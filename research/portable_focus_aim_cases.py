"""Literal camera/marker/target stimuli; no precomputed native aim schedule."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo_fixtures
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def original_fixtures():
    seed=copy.deepcopy(ammo_fixtures()[0]);seed.pop('contract');rows=[]
    def add(label,value=1,owner=0,target='all_allies',camera=(0,),layer2=True):
        c=copy.deepcopy(seed);c['name']='focus-aim-'+label
        c['focus_aim_layer2']=layer2;c['camera']=[roster_names(c)[i] for i in camera]
        c['camera_mode']='shared' if len(camera)>1 else 'single'
        c['environment']['focus_aim_layer2']=layer2
        c['combat']['weapons'][1].update(mode='auto',interval=.1,min_cycle=.1,capacity=10)
        c['effects']=[field('crit_rate',-100,'all_allies','no-crit'),field('focus_fire',value,target,'focus-marker')]
        c['owners']=[0,owner]
        c['patterns']=[dict(id='stop',kind='interrupt',targets=[dict(name='stop',hp=1e8)]),
                       dict(id='adds',kind='summon',spec=dict(count=1,hp=1e8,atk=1))]
        rows.append(c);return c
    add('all')
    add('zero',value=0)
    add('negative',value=-1)
    c=add('absent');c['effects'][-1]['trigger']['condition']=['self_hp_below:0']
    add('recipient-self',owner=1,target='self')
    c=add('foreign-recipient');c['effects'][-1]['target']=roster_names(c)[4]
    c=add('name-is-not-stat');c['effects'][-1].update(stat='atk_pct',fixed_value=0,name='focus_fire')
    c=add('expires');c['effects'][-1]['duration']=.1
    c=add('arrives');c['effects'][-1]['trigger']['timing']=['every:0.1s'];c['effects'][-1]['max_trigger']=1
    c=add('unfocused-runtime',owner=1);c['effects'][-1]['trigger']['condition']=['focusing']
    c=add('focused-runtime');c['effects'][-1]['trigger']['condition']=['focusing']
    c=add('finite-unfocused-snapshot',owner=1);c['effects'][-1].update(duration=.2);c['effects'][-1]['trigger']['condition']=['focusing']
    add('empty-camera',camera=())
    add('layer-one',layer2=False)
    add('shared-camera',camera=(0,1))
    c=add('interrupt-expires');c['patterns'][0]['until']={'time':.15}
    c=add('same-frame-destruction');c['patterns'][0]['targets'][0]['hp']=1
    c=add('penalty-part');c['patterns']=[dict(id='parts',kind='parts',until=dict(targets_cleared=True,time=.2),targets=[dict(name='penalty',hp=1e8)]),dict(id='failure',kind='idle',after=[dict(node='parts',outcome='expired')])]
    return rows


def fixtures():
    # Keep physical-interrupt originals available for the native model-gap audit.
    originals=original_fixtures();rows=[]
    for c in originals:
        if c['name'].endswith(('same-frame-destruction','penalty-part')):continue
        c['name']+='-aim-only'
        for w in c['combat']['weapons']:w.update(mode='charge',charge=10,interval=10,min_cycle=10)
        rows.append(c)
    for label,changes in [('all',{}),('zero',{'fixed_value':0}),('negative',{'fixed_value':-1}),('absent',{'trigger':dict(timing=['battle_start'],condition=['self_hp_below:0'])}),('expires',{'duration':.1})]:
        c=copy.deepcopy(originals[-1]);c['name']='focus-aim-penalty-weapon-'+label;c['duration']=.15
        c['effects'][-1].update(changes);rows.append(c)
    c=copy.deepcopy(rows[-5]);c['name']='focus-aim-penalty-weapon-same-frame-destruction';c['patterns'][0]['targets'][0]['hp']=1;rows.append(c)
    from portable_state_predicate_cases import fixtures as predicate_fixtures
    c=copy.deepcopy(next(c for c in predicate_fixtures() if c['name'].endswith('focus-dynamic-owner')))
    c.pop('contract');c['name']='focus-aim-numeric-cache-live-marker'
    c['focus_aim_layer2']=True;c['environment']['focus_aim_layer2']=True
    c['effects'][0]['target']='all_allies'
    c['effects'].append(field('focus_fire',0,'all_allies','live-focus',timing='passive',condition=['focusing']));c['owners'].append(0)
    c['patterns']=[dict(id='parts',kind='parts',until=dict(targets_cleared=True,time=1),targets=[dict(name='penalty',hp=1e8)]),dict(id='failure',kind='idle',after=[dict(node='parts',outcome='expired')])]
    rows.append(c)
    c=copy.deepcopy(c);c['name']='focus-aim-numeric-cache-epoch'
    c['controls'][1]={};c['combat']['weapons'][1].update(mode='auto',interval=.1,min_cycle=.1,capacity=10)
    c['effects'][1]['target']='all_allies'
    c['effects'].append(dict(field('atk_pct',0,'self','epoch-change',timing='on_attack'),max_trigger=1));c['owners'].append(0)
    rows.append(c)
    return rows
