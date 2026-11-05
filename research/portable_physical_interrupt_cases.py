"""Authored physical interception contracts, independent of GPU output."""
import copy,math
from portable_parts_skill_cases import fixtures as originals
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    seed=next(c for c in originals() if c['name']=='parts-skill-interrupt-only');rows=[]
    def add(label,damage,intercept,*,charge=True,wide=False,pierce=False,pellets=1,muzzles=1):
        c=copy.deepcopy(seed);c.update(name='interrupt-weapon-'+label,duration=.08)
        c['effects']=c['effects'][:-1];c['owners']=c['owners'][:-1]
        c['weapon_metadata']['fire_stance_hold']=0
        c['patterns']=[dict(id='parts',kind='parts',targets=[dict(name='part-near',hp=1e8,reach=1),dict(name='part-far',hp=1e8,reach=4)]),dict(id='interrupt',kind='interrupt',targets=[dict(name='stop-near',hp=1e8,reach=1),dict(name='stop-far',hp=1e8,reach=4)])]
        c['combat']['weapons'][0].update(mode='charge' if charge else 'auto',base_weapon_type='RL' if charge else 'AR',coefficient=100,interval=.1,min_cycle=.1,charge=.05,pellets=pellets,muzzles=muzzles,full_charge_mult=100)
        c['contract']=dict(damage=[damage,0,0,0,0],interrupt_damage=[intercept,0,0,0,0],packet_damage=[],packet_parts=[],named_hit_notices=0,event_kinds=[],gauge=0)
        def buff(stat,value,name,timing='battle_start'):c['effects'].append(field(stat,value,'self',name,timing=timing));c['owners'].append(0)
        if pierce:buff('pierce_enabled',1,'pierce')
        if wide:buff('explosion_range' if charge else 'pierce_range',100,'wide')
        rows.append(c);return c,buff
    add('rl-near',5000,2000)
    add('rl-wide',8000,4000,wide=True)
    add('ar-pierce',5000,2000,charge=False,pierce=True)
    c,_=add('sr-wide',8000,4000,charge=False,pierce=True,wide=True)
    c['combat']['weapons'][0]['base_weapon_type']='SR'
    for p in c['patterns']:p['targets'][1]['reach']=2
    c,_=add('scatter-two-muzzles',10002,4002,charge=False,pierce=True,pellets=3,muzzles=2);c['combat']['weapons'][0]['base_weapon_type']='SG'
    c,buff=add('scatter-child-snapshot',26004,19998,charge=False,pierce=True,pellets=3,muzzles=2);c['duration']=.15;c['combat']['weapons'][0]['base_weapon_type']='SG'
    for p in c['patterns']:p['targets'][1]['reach']=2
    buff('pierce_range',100,'next-range','pellet_hit_count:1');buff('intercept_dmg_pct',100,'next-intercept','pellet_hit_count:1')
    c,buff=add('heal-child-snapshot',5000,2000)
    c['effects'].insert(0,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(0,0)
    buff('lifesteal_pct',10,'lifesteal');buff('intercept_dmg_pct',100,'intercept-after-heal','event:heal_received');buff('part_dmg_pct',100,'part-after-heal','event:heal_received')
    c['contract']['hp']=[5700,5000,5000,5000,5000]
    c,buff=add('destroy-group',5000,4000)
    c['patterns'][1]['targets']=[dict(name='stop-a',hp=1,reach=1,score=7),dict(name='stop-b',hp=1,reach=1,score=9)]
    c['effects'].insert(0,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(0,0);buff('lifesteal_pct',10,'lifesteal');c['contract']['hp']=[5900,5000,5000,5000,5000]
    c,_=add('unbreakable',5000,2000);c['patterns'][1]['targets'][0]['hp']=0
    c,_=add('vanish-gate',0,0);c['patterns'].append(dict(id='hidden',kind='vanish',until=dict(time=.2)))
    c,_=add('add-first-pellet-death',8335,3335,charge=False,pierce=True,pellets=3,muzzles=2);c['combat']['weapons'][0]['base_weapon_type']='SG';c['patterns'].append(dict(id='add',kind='summon',spec=dict(count=1,hp=1)))
    add('no-reach',2000,0,charge=False)
    c,buff=add('range-before-threshold',5000,2000);buff('explosion_range',math.nextafter(100.-1e-9,-math.inf),'threshold')
    c,buff=add('range-at-threshold',8000,4000);buff('explosion_range',100.-1e-9,'threshold')
    for label,intercept,critical,damage,extra in [('core',0,False,7000,2000),('core-intercept',50,False,7000,3000),('core-critical-intercept',50,True,9500,4500)]:
        c,buff=add(label,damage,extra,charge=False,pierce=True);c['enemy']['core_px']=1e8
        if intercept:buff('intercept_dmg_pct',intercept,'intercept-factor')
        if critical:c['effects'][0]['fixed_value']=100
    return rows
