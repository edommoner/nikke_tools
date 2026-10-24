"""Authored mode/reload/click/pellet compositions with the same frame aim IR."""
import copy
from portable_coordinate_aim_cases import fixtures as aims
from world_enemy_attack_cases import field


def fixtures():
    seeds={c['name'].split('/')[-1]:c for c in aims()};rows=[]
    def add(label,seed='anchor-reload-minus'):
        c=copy.deepcopy(seeds[seed]);c.update(name='coordinate-core/control/'+label,duration=.75)
        rows.append(c);return c
    def effect(c,e,owner=0):c['effects'].append(e);c['owners'].append(owner)
    def mode(c,reload=.05,start=0.,duration=1.):
        e=dict(name='control-weapon',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=150,max_ammo=-1,fire_rate=10,fire_rate_max=10,charge=False,charge_time=.2,full_charge_mult=100,pellets=3,muzzles=2,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,skill_damage=True,reload_time=reload,target='self',duration=duration,trigger=dict(timing=['battle_start'] if start==0 else ['every:'+str(start)+'s'],condition=[]),max_trigger=1)
        effect(c,e)
    c=add('mode-short-reload');mode(c)
    c=add('mode-long-reload');mode(c,reload=2.)
    c=add('mode-late-entry');mode(c,start=.15,duration=.3)
    c=add('mode-expiry');mode(c,duration=.15)
    for ratio in (-50,-75):
        c=add('base-single-clip-ratio-'+str(-ratio));c['duration']=1.1
        c['combat']['weapons'][0].update(capacity=4,interval=.02,min_cycle=.02)
        c['controls'][0]['aim'][0].update(offset=1.7,len=.3)
        effect(c,field('reload_ratio_pct',ratio,'self','clip-ratio'))
    c=add('fixed-reload-and-ratio');c['duration']=.9
    c['combat']['weapons'][0].update(capacity=4,interval=.02,min_cycle=.02)
    effect(c,field('reload_ratio_pct',-75,'self','clip-ratio'));effect(c,field('reload_time_fixed',.1,'self','fixed-reload'))
    c=add('clip31-rounding');c['duration']=1.2
    c['combat']['weapons'][0].update(capacity=31,interval=.01,min_cycle=.01,clip_count=3)
    c['weapon_metadata']['clip_count']=3
    for w in c['combat']['weapons']:w['clip_count']=3
    c['controls'][0]['aim'][0].update(offset=2.2,len=.3)
    c=add('capacity-and-ratio');c['duration']=1.1
    c['combat']['weapons'][0].update(capacity=4,interval=.02,min_cycle=.02)
    c['controls'][0]['aim'][0].update(offset=1.7,len=.3)
    effect(c,field('reload_ratio_pct',-75,'self','clip-ratio'));effect(c,field('max_ammo_pct',100,'self','larger-clip'))
    c=add('manual-seven-pellet-two-muzzle','manual-owner-only');c['combat']['weapons'][0].update(pellets=7,muzzles=2)
    c=add('manual-pellet-notification','manual-owner-only');c['combat']['weapons'][0].update(pellets=3,muzzles=2)
    effect(c,field('atk_pct',100,'self','after-part','part_hit_count:1',max_stack=128))
    c=add('manual-mode-scatter','manual-owner-only');mode(c,duration=.35)
    c=add('manual-mode-fraction-notification','manual-owner-only');mode(c,duration=.35)
    effect(c,field('atk_pct',100,'self','after-part','part_hit_count:1',max_stack=128))
    c=add('aim-and-tap','manual-owner-only');c['combat']['weapons'][0].update(mode='charge',charge=.05,interval=.1,min_cycle=.1,full_charge_mult=100)
    c['controls'][0]['click']=[dict(mode='tap',window='always',priority=20,rate=10)]
    c=add('aim-and-own-hold','full-burst-follow')
    c['combat']['weapons'][0].update(mode='charge',charge=.05,interval=.1,min_cycle=.1,full_charge_mult=100)
    c['controls'][0]['click']=[dict(mode='hold_until_close',window='burst_chain',priority=30)]
    c=add('competing-hold-owner','full-burst-follow')
    c['controls'][0]['aim'][0]['priority']=10
    c['combat']['weapons'][1].update(charge=.05,interval=.1,min_cycle=.1,full_charge_mult=100)
    c['controls'][1]=dict(click=[dict(mode='hold_until_close',window='burst_chain',priority=30)])
    for c in rows:
        for weapon in c['combat']['weapons']:
            weapon.setdefault('pellets',1);weapon.setdefault('muzzles',1)
    return rows
