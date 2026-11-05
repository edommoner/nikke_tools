"""Literal partial-charge stimuli; no packing or reference work on import."""
import copy
from world_charge_control_cases import fixtures as charge_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field


def fixtures():
    base=copy.deepcopy(charge_fixtures()[0]);base.update(effects=[],owners=[],duration=.95,state_queries=[],controls=[{} for _ in range(5)])
    base['combat']['initial_gauge']=0
    for ally in base['environment']['allies']:ally['base_hp']=10000
    base['patterns']=[dict(id='idle',kind='idle')]
    rows=[]
    def add(label,threshold='3',owner=0,tap=True,activations=1,partial=3,full=0):
        c=copy.deepcopy(base);c['name']='nonfull-charge-'+label
        if tap:c['controls'][owner]=dict(click=[dict(window='always',mode='tap',rate=4,release=.05)])
        e=instant('heal_hp_pct',1,'self','nonfull-watch','non_full_charge_fire_count:'+threshold)
        c.update(effects=[instant('current_hp_reduce',50,'all_allies','drain'),e],owners=[0,owner],contract=dict(owner=owner,partial=partial,full=full,activations=activations,hp=[5000+100*activations if i==owner else 5000 for i in range(5)]));rows.append(c);return c
    add('every-third')
    add('every-shot','1',activations=3)
    add('every-second','2',activations=1)
    add('threshold-not-reached','5',activations=0)
    add('automatic-full-only',tap=False,partial=0,full=2,activations=0)
    add('last-owner',owner=4)
    c=add('other-owner',activations=0);c['owners']=[0,4]
    c=add('all-recipients');c['effects'][-1]['target']='all_allies';c['contract']['hp']=[5100]*5
    c=add('budget',threshold='1',activations=1);c['effects'][-1]['max_trigger']=1
    c=add('false-condition',threshold='1',activations=0);c['effects'][-1]['trigger']['condition']=['during_full_burst']
    c=add('duplicate-descriptor',activations=2);c['effects'][-1]['trigger']['timing']*=2
    c=add('raw-alias',activations=2);c['effects'][-1]['trigger']['timing']+=['non_full_charge_fire_count:03']
    c=add('mixed-attack',activations=4);c['effects'][-1]['trigger']['timing']+=['on_attack']
    c=add('reduce-threshold',activations=3);c['effects'].insert(0,field('trigger_count_reduce',2,'self','reducer',target_effect='nonfull-watch'));c['owners'].insert(0,0)
    add('zero-clamped','0',activations=3)
    add('negative-clamped','-1',activations=3)
    add('unresolved-template','{0}',activations=0)
    c=add('slow-tap-still-partial',partial=2,full=0,activations=0);c['controls'][0]['click'][0]['rate']=2
    c=add('periodic-full',partial=1,full=2,activations=1,threshold='1');c['controls'][0]['click'][0]['full_charge_interval']=.3
    c=add('slow-tap-genuine-full',partial=0,full=1,activations=0);c['duration']=1.5;c['controls'][0]['click'][0]['rate']=1
    c=add('scatter-muzzles',threshold='1',activations=3);c['combat']['weapons'][0].update(pellets=3,muzzles=2)
    c=add('reload-between-taps',threshold='1',partial=2,activations=2);c['combat']['weapons'][0].update(capacity=1,reload=.2)
    c=add('callback-auto-mode',threshold='1',partial=2,activations=2)
    mode=copy.deepcopy(next(x for x in charge_fixtures() if x['name']=='manual-charge-callback-enters-auto-mode')['effects'][0]);mode.update(name='nonfull-auto-mode',trigger=dict(timing=['non_full_charge_fire_count:1'],condition=[]));c['effects'].append(mode);c['owners'].append(0);c['contract']['auto_shots']=3
    return rows
