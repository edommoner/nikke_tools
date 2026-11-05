"""Literal per-shot pellet contracts, independent of packing and GPU output."""
import copy
from portable_lost_hp_attack_cases import fixtures as lost_fixtures
from world_enemy_attack_cases import field


def fixtures():
    base=copy.deepcopy(lost_fixtures()[-1])
    base.update(effects=[],owners=[],patterns=[dict(id='idle',kind='idle')],base_atk=[6000]*5,duration=.25)
    for weapon in base['combat']['weapons']:weapon.update(mode='charge',charge=10,interval=10)
    rows=[]
    def add(label,*,pellets=5,muzzles=1,timings=('pellet_hit_in_shot:5',),notices=('5',),stack=3,damages=(1200,1320,1440),owner=0):
        c=copy.deepcopy(base);c['name']='pellet-shot-'+label
        c['combat']['weapons'][owner].update(mode='auto',interval=.1,pellets=pellets,muzzles=muzzles,capacity=10)
        watch=field('atk_pct',10,'self','shot-watch',max_stack=128)
        watch['trigger']['timing']=list(timings)
        c.update(effects=[field('crit_rate',-100,'self','no-crit'),watch],owners=[owner,owner])
        c['contract']=dict(owner=owner,notices=list(notices)*3,counts=[pellets*muzzles]*(len(notices)*3),stacks={'shot-watch':stack},packet_damage=list(damages),packet_counts=[pellets*muzzles]*3)
        rows.append(c);return c
    add('equal')
    add('below',pellets=4,notices=(),stack=0,damages=(1500,1500,1500))
    add('above',pellets=6,damages=(1000,1100,1200))
    add('across-muzzles',pellets=3,muzzles=2,damages=(2000,2200,2400))
    add('not-cumulative',pellets=3,timings=('pellet_hit_in_shot:6',),notices=(),stack=0,damages=(2000,2000,2000))
    add('last-owner',owner=4)
    add('zero',timings=('pellet_hit_in_shot:0',),notices=('0',))
    add('negative',timings=('pellet_hit_in_shot:-1',),notices=('-1',))
    add('signed-minimum',timings=('pellet_hit_in_shot:-2147483648',),notices=('-2147483648',))
    add('large',timings=('pellet_hit_in_shot:2147483647',),notices=(),stack=0,damages=(1200,1200,1200))
    add('raw-aliases',timings=tuple('pellet_hit_in_shot:'+x for x in ('5','05','+5',' 5','５')),notices=(' 5','+5','05','5','５'),stack=15,damages=(1200,1800,2400))
    add('numeric-order',timings=('pellet_hit_in_shot:5','pellet_hit_in_shot:2','pellet_hit_in_shot:10'),notices=('2','5'),stack=6,damages=(1200,1440,1680))
    add('duplicate-descriptor',timings=('pellet_hit_in_shot:5',)*2,stack=6,damages=(1200,1440,1680))
    add('mixed-on-attack',timings=('pellet_hit_in_shot:5','on_attack'),stack=6,damages=(1200,1440,1680))
    c=add('two-listeners',damages=(1200,1440,1680));c['effects'].append(dict(copy.deepcopy(c['effects'][1]),name='shot-watch-2'));c['owners'].append(0);c['contract']['stacks']['shot-watch-2']=3
    c=add('limited',stack=1,damages=(1200,1320,1320));c['effects'][1]['max_trigger']=1
    c=add('false-condition',stack=0,damages=(1200,1200,1200));c['effects'][1]['trigger']['condition']=['self_hp_below:1']
    c=add('expiry',stack=2,damages=(1200,1200,1320));c['effects'][1]['duration']=.1
    c=add('captured-count',pellets=3,notices=(),stack=2,damages=(2000,1000,1100))
    c['effects'].append(field('pellet_count',3,'self','split-child','pellet_hit',max_stack=1));c['owners'].append(0)
    c['contract'].update(notices=['5','5'],counts=[6,6],packet_counts=[3,6,6])
    c=add('charge-does-not-notify',notices=(),stack=0,damages=(1200,1200))
    c['combat']['weapons'][0].update(mode='charge',charge=.05,min_cycle=.1,full_charge_mult=100)
    c['contract']['packet_counts']=[5,5]
    c=add('warmup');c['combat']['weapons'][0].update(mode='auto_warmup',rate=10,rate_max=10,warmup=1)
    return rows
