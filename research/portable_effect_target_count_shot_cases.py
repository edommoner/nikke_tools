"""Original two-shot modifier and explicitly separate timing/recipient probes."""
import copy
from portable_heavyarms_lock_cases import source_definitions
from world_projectile_cases import fixtures as projectile_cases

def fixtures():
    seed=copy.deepcopy(projectile_cases()[0]);original=source_definitions()[20]
    seed.update(duration=.6,effects=[original,dict(name='start-burst',source='스킬1',type='instant',stat='burst_charge_pct',fixed_value=100,target='self',trigger=dict(timing=['battle_start'],condition=[]))],owners=[0,0])
    for i,w in enumerate(seed['combat']['weapons']):w.update(stage=[3,1,2,0,0][i],gauge=0)
    rows=[]
    def add(name,original_definition=True):
        c=copy.deepcopy(seed);c.update(name='target-count-physical/'+name,target_count_original_definition=original_definition);rows.append(c);return c
    add('original-auto-pellets-muzzles')
    c=add('original-charge');c['duration']=1.2
    c['combat']['weapons'][0].update(mode='charge',base_weapon_type='SR',charge=.1,interval=.3,min_cycle=.3,full_charge_mult=100,gauge_mult=100)
    c['post_fire_delays'][0]=.215
    c=add('battle-start-same-frame',False);c['effects'][0]['trigger']['timing']=['battle_start']
    c=add('attack-bound-same-frame',False);c['effects'][0]['trigger']['timing']=['on_attack'];c['effects'][0]['max_trigger']=1
    c=add('allied-independent-clocks',False);c['duration']=.9;c['effects'][0].update(target='all_allies');c['effects'][0]['trigger']['timing']=['battle_start']
    c['combat']['weapons'][1]['interval']=.3
    return rows
