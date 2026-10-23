"""One native/CUDA/Metal table driven by the actual battle scheduler."""
import copy
from portable_projectile_chain_cases import fixtures as prior
from world_enemy_attack_cases import field

def fixtures():
    seed=copy.deepcopy(prior()[0]);seed.update(name='',duration=.4,effects=[],owners=[])
    seed.update({k:False for k in seed if k.startswith('observe_')});seed['observe_overlay']=True
    rows=[]
    def add(name,*,timing='battle_start',repeat=False):
        c=copy.deepcopy(seed);c.update(name='destructible-battle/'+name,typed_bindings=[dict(node='idle',kind=2,identity=10,capacity=10000.)],max_attacks=128)
        c['patterns']=[dict(id='idle',kind='idle',until=dict(time=.1 if repeat else 1.))]
        if repeat:c['patterns'][0].update(after=['start','idle'],repeat=3,emit=['event:target_spawn'])
        c['effects']=[dict(name='typed-source',source='스킬3',type='damage',stat='damage',fixed_value=100.,target='all_projectiles',trigger=dict(timing=[timing],condition=[]))];c['owners']=[0]
        rows.append(c);return c
    add('plain')
    add('three-real-generations',timing='event:target_spawn',repeat=True)
    c=add('empty');c['patterns'][0]['delay']=1.
    c=add('physical-and-typed',timing='every:0.1s');c['effects'][0]['max_trigger']=2
    c['combat']['weapons'][0].update(mode='auto',interval=.1,min_cycle=.1,post_reload_delay=0);c['post_fire_delays'][0]=0
    c=add('ordinary-named-child');child=copy.deepcopy(c['effects'][0]);child.update(name='body-child',target='boss',fixed_value=50.,trigger=dict(timing=['weapon_hit:typed-source'],condition=[]));c['effects'].append(child);c['owners'].append(0)
    c=add('high-slot128');c['typed_bindings']=[dict(node='idle',kind=2,identity=10+i,capacity=10000.) for i in range(128)]
    c=add('broken-set-not-retargeted',timing='every:0.1s');c['typed_bindings'][0]['capacity']=500.
    c=add('projectiles-with-shields');c['typed_bindings'].extend([dict(node='idle',kind=3,identity=20,capacity=5000.),dict(node='idle',kind=4,identity=21,capacity=5.)])
    c=add('live-buff-and-expiry',timing='every:0.1s');c['effects'].insert(0,field('atk_pct',50,'self','live-atk',duration=.15));c['owners'].insert(0,0)
    c=add('empty-retains-budget',timing='every:0.1s');c['patterns'][0]['delay']=.15;c['effects'][0]['max_trigger']=1
    return rows
