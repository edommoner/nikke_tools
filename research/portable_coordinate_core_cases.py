"""Literal core lifecycle/geometry worlds; no selected core or probability IR."""
import copy
from portable_coordinate_physical_gpu_cases import fixtures as physical
from portable_coordinate_quantity_cases import fixtures as quantities
from world_enemy_attack_cases import field

def fixtures():
    base=physical()[0];rows=[]
    def add(label,diameter=4,x=0,y=0,auto=False,pierce=False,parts=True):
        case=copy.deepcopy(base);case['name']='coordinate-core/'+label;case['duration']=.25;case['observe_coordinate_landings']=True
        if not parts:case['patterns']=[dict(id='idle',kind='idle')]
        case['patterns'].append(dict(id='core',kind='core',core_px=diameter,x=x,y=y))
        if auto:case['enemy']['coord'].pop('auto_aim',None)
        if pierce:case['effects'].append(field('pierce_enabled',1,'self','core-pierce'));case['owners'].append(0)
        rows.append(case);return case
    add('centered-core',parts=False)
    c=add('base-core',parts=False);c['patterns'].pop();c['enemy']['core_px']=4
    add('off-center-explicit',x=3,y=-1,parts=False)
    add('off-center-default-auto',x=3,y=-1,auto=True,parts=False)
    add('part-occlusion')
    add('pierce-under-part',pierce=True)
    c=add('explosion-under-part');c['combat']['weapons'][0].update(mode='charge',charge=.05,interval=.1,min_cycle=.1,full_charge_mult=100);c['combat']['weapons'][0]['base_weapon_type']='RL';c['post_fire_delays'][0]=.215
    c=add('critical-and-core-damage',parts=False);c['effects'][0]['fixed_value']=25;c['effects'].append(field('core_dmg_pct',50,'self','core-factor'));c['owners'].append(0)
    c=add('core-fraction-child',diameter=12,parts=False);c['effects'].append(field('atk_pct',10,'self','core-notice','core_hit_count:1',max_stack=8));c['owners'].append(0)
    c=add('delayed-open',x=7,auto=True);c['patterns'][-1]['delay']=.1
    c=add('expiry',auto=True);c['patterns'][-1]['until']=dict(time=.1)
    c=add('reopen',auto=True);c['patterns'][-1].update(after=['start','core'],until=dict(time=.05),repeat=0,delay=.05)
    c=add('largest-wins',diameter=8,x=4,auto=True);c['patterns'].append(dict(id='smaller-newer',kind='core',core_px=4,x=-5,y=2,delay=.1))
    c=add('equal-newest-start',x=4,auto=True);c['patterns'].append(dict(id='equal-newer',kind='core',core_px=4,x=-5,y=2,delay=.1))
    c=add('equal-declaration-order',x=4,auto=True);c['patterns'].append(dict(id='equal-later',kind='core',core_px=4,x=-5,y=2))
    c=add('base-equal-node',x=4,auto=True);c['enemy']['core_px']=4
    c=add('base-larger-than-node',x=4,auto=True);c['enemy']['core_px']=8
    c=add('older-declaration-newest-start',x=4,auto=True);c['patterns'][-1]['delay']=.1;c['patterns'].append(dict(id='equal-earlier-start',kind='core',core_px=4,x=-5,y=2))
    c=add('winner-expires-restores-core',x=4,auto=True);c['patterns'][-1]['until']=dict(time=.1);c['patterns'].insert(-1,dict(id='older-core',kind='core',core_px=4,x=-5,y=2))
    c=add('large-core',diameter=100,parts=False)
    c=add('tiny-core',diameter=1,parts=False)
    c=add('scatter-two-muzzles',pierce=True);c['combat']['weapons'][0].update(pellets=3,muzzles=2)
    c=add('two-shooters',auto=True,x=4,pierce=True);c['combat']['weapons'][3]=copy.deepcopy(c['combat']['weapons'][0])
    c=add('last-owner',parts=False);c['combat']['weapons'][4]=copy.deepcopy(c['combat']['weapons'][0]);c['combat']['weapons'][0].update(mode='charge',charge=10,interval=10,min_cycle=10);c['owners']=[4]*len(c['owners'])
    c=copy.deepcopy(quantities()[0]);c['name']='coordinate-core/expanded-parent';c['patterns'].append(dict(id='core',kind='core',core_px=4,x=0,y=0));rows.append(c)
    c=add('32-nodes',parts=False,auto=True,x=3);c['patterns']=[dict(id='idle-'+str(i),kind='idle') for i in range(31)]+[c['patterns'][-1]]
    c=add('127-targets',parts=False);c['patterns'][0]=dict(id='parts',kind='parts',targets=[dict(name='far-'+str(i),hp=1e8,x=1000+i*5,y=1000,r=1,z=i) for i in range(127)])
    c=add('area-skill-default-core-aim',auto=True,x=40,y=0,pierce=True);c['patterns'][0]['targets'][1].update(x=40)
    c['effects'].append(dict(name='core-area-skill',source='스킬2',type='damage',stat='pierce_damage',fixed_value=100,target='target_body',trigger=dict(timing=['every:0.1s'],condition=[]),max_trigger=1));c['owners'].append(0)
    return rows
