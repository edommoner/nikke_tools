"""Authored manual-charge contracts, including owner arbitration and callbacks."""
import copy
from world_team_cases import fixtures as team_fixtures
from world_enemy_attack_cases import field

def fixtures():
 base=copy.deepcopy(team_fixtures()[0]);base.update(duration=1.4,controls=[{} for _ in range(5)],camera=[],control_mode='solo');base['patterns']=[dict(id='idle',kind='idle',until=dict(time=1.4))]
 for w in base['combat']['weapons']:w.update(mode='charge',base_weapon_type='SR',charge=.2,interval=.4,min_cycle=0,full_charge_mult=300,gauge_mult=100,gauge=.25)
 base['post_fire_delays']=[.215]*5;base['weapon_metadata']=dict(input_type='UP')
 base['effects']=[field('atk_pct',1,'self','held','charge_hold:0.1',max_stack=128)];base['owners']=[0];base['state_queries']=[(0,0,0,1,'held')];rows=[]
 def add(name):
  c=copy.deepcopy(base);c['name']='manual-charge-'+name;rows.append(c);return c
 def sequence(c,who=0,until=.8,at=0):c['controls'][who]=dict(sequence=[dict(action='hold',t=at,until=until)])
 for threshold in ('0','0.1','0.5'):
  c=add('automatic-'+threshold);c['effects'][0]['trigger']['timing']=['charge_hold:'+threshold]
 for until in (.3,.5,.8,1.2):
  c=add('sequence-until-'+str(until));sequence(c,until=until)
 c=add('raw-alias-order');sequence(c);c['effects']=[field('atk_pct',1,'self',raw.replace('.','_'),'charge_hold:'+raw,max_stack=128) for raw in ('0.10','0.1','0.2','0')];c['owners']=[0]*4;c['state_queries']=[(0,0,0,1,c['effects'][0]['name'])]
 c=add('repeated-charge-count');sequence(c,until=.5);c['controls'][0]['sequence'] += [dict(action='hold',t=.7,until=1.2),dict(action='hold',t=1.4,until=2)];c['effects'][0]['trigger']['timing']=['charge_hold_count:0.1:2'];c['duration']=2.6
 c=add('sequence-release-none');sequence(c,until=1.2);c['controls'][0]['sequence'].append(dict(action='hold',t=.5))
 c=add('completed-charge-survives-speed-expiry');sequence(c);c['effects'][0]['trigger']['timing']=['charge_hold:0.2'];c['effects'].append(field('charge_speed_pct',100,'self','temporary-speed','battle_start',duration=.15));c['owners'].append(0)
 c=add('callback-latches-before-later-threshold');sequence(c);c['effects'][0].update(stat='charge_speed_pct',fixed_value=-50);c['effects'].append(field('atk_pct',1,'self','second-held','charge_hold:0.2',max_stack=128));c['owners'].append(0)
 c=add('callback-removes-ammo-while-holding');sequence(c);c['effects'][0].update(type='instant',stat='ammo_charge_pct',fixed_value=-100,max_trigger=1)
 c=add('owner-down-while-holding');sequence(c);c['patterns'].append(dict(id='kill-holder',kind='attack',delay=.4,spec=dict(atk=10000000,coeff=100,target='slot:1',hits=1)))
 c=add('callback-enters-auto-mode');sequence(c);c['effects'][0]=dict(name='held',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=100,max_ammo=-1,fire_rate=10,fire_rate_max=10,charge=False,pellets=1,muzzles=1,post_fire_delay=0,burst_energy=.25,core_dmg_mult=200,skill_damage=True,target='self',duration=.3,max_trigger=1,trigger=dict(timing=['charge_hold:0.1'],condition=[]))
 for mode in ('solo','warn','strict'):
  c=add('simultaneous-'+mode);c['control_mode']=mode;sequence(c,0,.8);sequence(c,1,1);c['effects'].append(field('crit_dmg',1,'self','other-held','charge_hold:0.1',max_stack=128));c['owners'].append(1)
 c=add('same-priority-new-request-preempts');sequence(c,0,1);sequence(c,1,1.2,.4);c['effects'].append(field('crit_dmg',1,'self','other-held','charge_hold:0.1',max_stack=128));c['owners'].append(1)
 c=add('low-priority-request-cannot-preempt-sequence');sequence(c,0,1);c['controls'][1]=dict(click=[dict(mode='hold',window='always',priority='low')])
 for policy in ('own_full_burst','charge_hold_after_fb'):
  for condition in ('not_during_full_burst','during_full_burst'):
   c=add(policy+'-'+condition);c['controls'][0]=dict(hold=dict(policy=policy,lead=.1));c['duration']=11.5;c['combat']['initial_gauge']=100
   for i in range(3):c['combat']['weapons'][i]['stage']=i+1
   c['effects'][0]['trigger']['condition']=[condition]
 c=add('state-window-closes-at-full-burst');c['controls'][0]=dict(click=[dict(mode='hold_until_close',window='burst_chain')]);c['combat']['initial_gauge']=100
 for i in range(3):c['combat']['weapons'][i]['stage']=i+1
 c=copy.deepcopy(next(c for c in rows if c['name']=='manual-charge-callback-enters-auto-mode'));c['name']='manual-charge-mode-entry-state-snapshot';c['duration']=.5;rows.append(c)
 c=copy.deepcopy(next(c for c in rows if c['name']=='manual-charge-sequence-until-0.8'));c['name']='manual-charge-critical-child-new-mode-snapshot';c['duration']=.81
 mode=copy.deepcopy(next(c for c in rows if c['name']=='manual-charge-callback-enters-auto-mode')['effects'][0]);mode['name']='critical-mode';mode['trigger']['timing']=['crit_hit'];c['effects'] += [mode,field('crit_rate',200,'self','certain-critical','battle_start')];c['owners'] += [0,0];rows.append(c)
 c=copy.deepcopy(next(c for c in rows if c['name']=='manual-charge-state-window-closes-at-full-burst'));c['name']='manual-charge-state-window-open-snapshot';c['duration']=.15;rows.append(c)
 c=copy.deepcopy(next(c for c in rows if c['name']=='manual-charge-own_full_burst-during_full_burst'));c['name']='manual-charge-policy-reentry-only-once';c['duration']=3.2;sequence(c,1,1.5,1);sequence(c,2,2.5,2);rows.append(c)
 c=copy.deepcopy(next(c for c in rows if c['name']=='manual-charge-automatic-0'));c['name']='manual-charge-down-charge-automatic';c['weapon_metadata'].update(input_type='DOWN_Charge',fire_stance_hold=0);c['post_fire_delays']=[0.]*5
 for w in c['combat']['weapons']:w['min_cycle']=.4
 rows.append(c)
 c=copy.deepcopy(next(c for c in rows if c['name']=='manual-charge-sequence-until-0.8'));c['name']='manual-charge-auto-weapon-ignores-hold';c['post_fire_delays']=[0.]*5
 for w in c['combat']['weapons']:w.update(mode='auto',base_weapon_type='AR',interval=.1)
 rows.append(c)
 c=copy.deepcopy(next(c for c in rows if c['name']=='manual-charge-callback-removes-ammo-while-holding'));c['name']='manual-charge-ammo-removal-retains-charge-for-second-alias';c['effects'].append(field('atk_pct',1,'self','still-charging','charge_hold:0.10',condition=['during_charge']));c['owners'].append(0);rows.append(c)
 for c in rows:
  if c['combat'].get('initial_gauge')==100:
   c['combat']['initial_gauge']=0;c['effects'].append(dict(name='initial-gauge',source='스킬1',type='instant',stat='burst_charge_pct',fixed_value=100,target='all_allies',trigger=dict(timing=['battle_start'],condition=[])));c['owners'].append(0)
  c['observe_charge_control']=True;c['observe_enemy_spawn']=True
 return rows
