"""Literal full-world entry-reload workloads; no portable packing or battle work."""
import copy
from portable_persona_cases import fixtures as persona_fixtures
from world_enemy_attack_cases import field


def fixtures():
    base=copy.deepcopy(persona_fixtures()[0])
    base.update(effects=[],owners=[],duration=1.2,controls=[{} for _ in range(5)])
    for weapon in base['combat']['weapons']:
        weapon.update(mode='auto',base_weapon_type='AR',stage=0,gauge=0,capacity=1000,interval=.2,reload=.6,pellets=1,muzzles=1)
    rows=[]
    def add(name,*,owner=0,charge=False,effects=(),**change):
        mode=dict(name='entry-mode',source='스킬1',type='weapon_change',weapon_type='SR' if charge else 'AR',damage_coeff=100,max_ammo=1000,fire_rate=10,fire_rate_max=10,charge=charge,charge_time=.2,full_charge_mult=100,pellets=1,muzzles=1,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,reload_time=.9,entry_reload=True,target='self',trigger=dict(timing=['battle_start'],condition=[]))
        mode.update(change)
        c=copy.deepcopy(base);c.update(name='entry-reload-'+name,effects=[*copy.deepcopy(effects),mode],owners=[owner]*(len(effects)+1));rows.append(c);return c
    add('base-auto');add('base-charge',charge=True);add('owner4-auto',owner=4)
    add('absent',entry_reload=False)['effects'][-1].pop('entry_reload')
    add('false',entry_reload=False)
    for value in (-50,50,100,150):add('speed-'+str(value),effects=[field('reload_speed_pct',value,'self','speed')])
    add('speed-sum',effects=[field('reload_speed_pct',50,'self','speed-a'),field('reload_speed_pct',25,'self','speed-b')])
    for value in (0,.2,-.2):add('fixed-'+str(value),effects=[field('reload_time_fixed',value,'self','fixed')])
    add('fixed-max',effects=[field('reload_time_fixed',.2,'self','fixed-a'),field('reload_time_fixed',.4,'self','fixed-b')])
    add('fixed-ignores-speed',effects=[field('reload_time_fixed',.2,'self','fixed'),field('reload_speed_pct',100,'self','speed')])
    add('speed-expires-latched',effects=[field('reload_speed_pct',50,'self','speed',duration=.1)])
    add('speed-arrives-latched',effects=[field('reload_speed_pct',100,'self','speed',timing='every:0.1s',max_trigger=1)])
    add('fixed-expires-latched',effects=[field('reload_time_fixed',.4,'self','fixed',duration=.1)])
    add('fixed-arrives-latched',effects=[field('reload_time_fixed',.2,'self','fixed',timing='every:0.1s',max_trigger=1)])
    for delay in (0,.17):
        for label,effects in [('bare',[]),('speed',[field('reload_speed_pct',50,'self','speed')]),('fixed',[field('reload_time_fixed',.4,'self','fixed')])]:
            c=add('measured-'+str(delay)+'-'+label,effects=effects);c['entry_delays']=[dict(owner=0,name='entry-mode',value=delay)]
    add('finite-before-wait-end',duration=.2)
    c=add('reenter',duration=.2,trigger=dict(timing=['battle_start','every:0.4s'],condition=[]));c['duration']=1.1
    add('delayed-entry',max_trigger=1,trigger=dict(timing=['every:0.2s'],condition=[]))
    c=add('during-base-charge',max_trigger=1,trigger=dict(timing=['every:0.1s'],condition=[]));c['combat']['weapons'][0].update(mode='charge',base_weapon_type='SR',charge=.4,interval=.4,min_cycle=.4,full_charge_mult=100);c['post_fire_delays'][0]=0
    c=add('during-base-reload',max_trigger=1,trigger=dict(timing=['every:0.3s'],condition=[]));c['combat']['weapons'][0]['capacity']=1;c['duration']=1.2
    c=add('cover-delays-entry');c['controls'][0]=dict(sequence=[dict(action='cover',t=0,duration=.2)])
    c=add('cover-speed-expires-before-entry',effects=[field('reload_speed_pct',50,'self','speed',duration=.1)])
    c['controls'][0]=dict(sequence=[dict(action='cover',t=0,duration=.2)])
    c=add('cover-fixed-arrives-before-entry',effects=[field('reload_time_fixed',.2,'self','fixed',timing='every:0.1s',max_trigger=1)])
    c['controls'][0]=dict(sequence=[dict(action='cover',t=0,duration=.2)])
    c=add('cover-measured-entry-delay');c['controls'][0]=dict(sequence=[dict(action='cover',t=0,duration=.2)])
    c['entry_delays']=[dict(owner=0,name='entry-mode',value=.17)]
    add('named-child-before-first-query',effects=[field('reload_speed_pct',50,'self','child-speed',timing='event:entry-mode')])
    return rows
