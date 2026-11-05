"""Literal notification-only ammo accounting, before GPU admission."""
import copy
from portable_pellet_shot_cases import fixtures as shot_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field


def fixtures():
    base=copy.deepcopy(shot_fixtures()[0]);base.update(effects=[],owners=[])
    for weapon in base['combat']['weapons']:weapon.update(mode='charge',charge=10,interval=10,min_cycle=10)
    rows=[]
    def add(label,*,value=4,notices=12,stack=3,damage=(6000,6600,7200),owner=0,watcher=None,timing='on_attack',calls=3,pellets=1,muzzles=1):
        c=copy.deepcopy(base);c['name']='ammo-equivalent-'+label
        c['combat']['weapons'][owner].update(mode='auto',interval=.1,min_cycle=.1,pellets=pellets,muzzles=muzzles,capacity=10)
        c['effects']=[field('crit_rate',-100,'self','no-crit'),instant('squad_ammo_consume_as',value,'self','equivalent',timing),field('atk_pct',10,'self','ammo-watch','squad_ammo_consume:4',max_stack=128)]
        c['owners']=[owner,owner,owner if watcher is None else watcher]
        c['contract']=dict(owner=owner,watcher=c['owners'][-1],notices=notices,stack=stack,packet_damage=list(damage),packet_counts=[pellets*muzzles]*len(damage),ammo=10-len(damage),calls=calls,call_names=['equivalent']*calls,call_values=[float(value)]*calls)
        rows.append(c);return c
    add('four')
    c=add('level-value');c['effects'][1].pop('fixed_value');c['effects'][1]['values']={'1':1,'10':4}
    add('zero',value=0,notices=3,stack=0,damage=(6000,)*3)
    add('one',value=1,notices=3,stack=0,damage=(6000,)*3)
    add('negative',value=-3.9,notices=3,stack=0,damage=(6000,)*3)
    add('fraction',value=3.9,notices=9,stack=2,damage=(6000,6600,6600))
    add('next-below-five',value=4.999999999999999)
    add('five',value=5,notices=15)
    add('forty',value=40,notices=120,stack=30,damage=(6000,12000,18000))
    c=add('maximum',value=4096,notices=4096,stack=1,damage=(6000,),calls=1);c['duration']=.02;c['effects'][-1]['trigger']['timing']=['squad_ammo_consume:4096']
    add('battle-start',timing='battle_start',notices=6,stack=1,damage=(6600,)*3,calls=1)
    c=add('duplicate-descriptor',notices=21,stack=5,damage=(6000,7200,7800),calls=6);c['effects'][1]['trigger']['timing']=['on_attack']*2
    c=add('limited',notices=6,stack=1,damage=(6000,6600,6600),calls=1);c['effects'][1]['max_trigger']=1
    c=add('false-condition',notices=3,stack=0,damage=(6000,)*3,calls=0);c['effects'][1]['trigger']['condition']=['self_hp_below:1']
    add('last-owner',owner=4)
    add('cross-owner-global-counter',watcher=4,damage=(6000,)*3)
    add('scatter',pellets=5,damage=(1200,1320,1440))
    add('muzzles',pellets=3,muzzles=2,damage=(2000,2200,2400))
    c=add('charge',notices=8,stack=2,damage=(6000,6600),calls=2);c['combat']['weapons'][0].update(mode='charge',charge=.05)
    c=add('every-notice',stack=12,damage=(6600,9000,11400));c['effects'][-1]['trigger']['timing']=['squad_ammo_consume:1']
    c=add('charge-every-notice',notices=8,stack=8,damage=(6000,8400),calls=2);c['combat']['weapons'][0].update(mode='charge',charge=.05);c['effects'][-1]['trigger']['timing']=['squad_ammo_consume:1']
    c=add('infinite-ammo',notices=9,stack=2,damage=(6000,6000,6600));c['effects'].insert(0,field('infinite_ammo',1,'self','infinite'));c['owners'].insert(0,0);c['contract']['ammo']=10
    c=add('recursive-bounded',value=2,timing='squad_ammo_consume:1',notices=5,stack=1,damage=(6000,6600,6600),calls=2);c['effects'][1]['max_trigger']=2
    c=add('recursive-once',timing='squad_ammo_consume:1',notices=6,stack=1,damage=(6600,)*3,calls=1);c['effects'][1]['max_trigger']=1
    c=add('periodic',timing='battle_start',notices=9,stack=2);c['effects'][1].update(tick_interval=.1,duration=.25);c['contract']['tick_calls']=[False,True,True]
    groups={'zero':[1,1,1],'one':[1,1,1],'negative':[1,1,1],'fraction':[3,3,3],'five':[5,5,5],'forty':[40,40,40],'maximum':[4096],'battle-start':[4,1,1],'duplicate-descriptor':[7,7,7],'limited':[4,1,1],'false-condition':[1,1,1],'infinite-ammo':[3,3,3],'recursive-bounded':[3,1,1],'recursive-once':[4,1,1],'periodic':[1,4,4]}
    for c in rows:
        label=c['name'].removeprefix('ammo-equivalent-');contract=c['contract']
        contract['notice_groups']=groups.get(label,[4]*len(contract['packet_damage']))
        contract['extras_before_physical']=[True,False,False] if label=='battle-start' else [False,True,True] if label=='periodic' else [False]*len(contract['packet_damage'])
    return rows
