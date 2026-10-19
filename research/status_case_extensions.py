"""Cross-family authored status stimuli. No native schedules become GPU input."""
import copy

def cases(buff,immune,cleanse,notify,query,case):
 rows=[]
 def add(name,effects,script,**kw):rows.append(case(name,effects,script,**kw));return rows[-1]
 def on(e,event):e=copy.deepcopy(e);e['trigger']['timing']=[event];return e
 for polarity in ('beneficial','harmful_irremovable'):
  add('nonharmful-does-not-spend-'+polarity,[immune(),buff(polarity=polarity)],[notify(0),notify(.1,7),query(.1)])
 for missing in (False,True):
  e=immune();e.pop('fixed_value')
  if not missing:e['values']={'10':1.5}
  add('charge-valued-presence-'+str(missing),[e,buff()],[notify(0),notify(.1,7),notify(.2,7),notify(.3,7),query(.3)])
 for mode in ('plain','named','not-matching'):
  first=immune('debuff_immune' if mode=='plain' else 'debuff_immune:harm' if mode=='named' else 'debuff_immune:other');first['name']='unlimited'
  add('unlimited-before-count-'+mode,[immune(),first,buff()],[notify(0),notify(.1,7),query(.1)])
 e=immune('debuff_immune_count',name='');add('empty-name-charge-has-no-notice',[e,buff()],[notify(0),notify(.1,7),notify(.2,7),query(.2)])
 a=immune();a['target']='self';a['fixed_value']=2
 b=immune();b['target']='all_allies_excl_self';b['fixed_value']=1
 add('same-name-cap-is-per-recipient',[a,b,buff()],[notify(0),notify(.1,7),notify(.2,7),query(.2)])
 e=immune(max_stack=5,duration=-1)
 a=buff('first child',target='self',max_stack=10,trigger=dict(timing=['event:immune'],condition=[]))
 b=buff('second child',target='self',max_stack=10,trigger=dict(timing=['event:immune'],condition=[]))
 add('recharge-after-all-named-children',[e,a,b,buff(target='self')],[notify(0),notify(.05,7),notify(.1),query(.1),notify(.2,7),query(.2,1)])
 for target in ('self','all_allies'):
  seed=buff('hp reduction',stat='max_hp_pct',fixed_value=-10,max_stack=1)
  add('cleanse-derived-health-'+target,[seed,cleanse(target=target)],[notify(0,7),query(0),notify(.1,8),query(.1,1)])
 e=buff('late harm',target='all_allies',trigger=dict(timing=['event:full_reload'],condition=[]))
 periodic=cleanse(fixed_value=1,tick_interval=.25,duration=1,trigger=dict(timing=['on_attack'],condition=[]))
 add('periodic-cleanse-keeps-clock',[e,periodic],[[0,4,0,0,0,-1,0,0],notify(0),notify(.1,7),[.35,4,0,0,0,-1,0,0],query(.35),notify(.4),[.6,4,0,0,0,-1,0,0],query(.6,1)])
 for stat in ('debuff_immune','debuff_immune_count'):
  e=immune(stat,target='all_enemies',fixed_value=2)
  h=buff(target='all_enemies',stat='received_dmg_pct')
  c=add('stale-enemy-charge-'+stat,[e,h],[notify(0),notify(.1,7),[.2,22,0,0,1,-1,0,0],[.3,21,0,0,1,-1,100000,0],notify(.4,7),query(.4,0,1),query(.4,1,0)])
  c['combat']['targets']=[dict(hp=100000),dict(hp=100000,kind=5,identity=0)]
 for mode in ('single','shared','captured-reference'):
  dot=dict(name='dot',source='스킬1',type='damage',stat='dot_damage',fixed_value=1,target='all_enemies' if mode=='shared' else 'boss',duration=2,max_stack=5,polarity='harmful',tick_interval=.5,scaling='stack_count',trigger=dict(timing=['event:full_reload'],condition=[]))
  effects=[dot,cleanse(target='boss',trigger=dict(timing=['on_attack'],condition=[]))]
  if mode=='captured-reference':
   dot['scaling_ref']='ref';effects.insert(0,buff('ref',fixed_value=1,polarity='beneficial',target='self',trigger=dict(timing=['event:full_reload'],condition=[])))
   effects.append(dict(name='increase reference',source='스킬2',type='instant',stat='buff_stack_add',fixed_value=2,target='self',target_effect='ref',trigger=dict(timing=['hit_count'],condition=[])))
  c=add('cleanse-dot-retains-clock-'+mode,effects,[[0,4,0,0,0,-1,0,0],notify(0),notify(.1,7),[.5,4,0,0,0,-1,0,0],query(.5),notify(.6),[1,4,0,0,0,-1,0,0],query(1,1)])
  
  if mode=='captured-reference':c['script'].insert(3,notify(.2,8))
  c['status_damage_reference']=True;c['combat']['targets']=[dict(hp=100000),dict(hp=100000,kind=5,identity=0)]
 for missing in (False,True):
  a=immune(name='A',fixed_value=0)
  if missing:a.pop('fixed_value')
  b=immune(name='B');a2=immune(name='A',fixed_value=2)
  add('first-valued-group-order-'+str(missing),[a,b,a2,buff()],[notify(0),notify(.05,19,1),notify(.1,7),query(.1)],owners=[0,0,1,0])
 a=immune();b=immune(fixed_value=2)
 add('same-name-pools-across-owners',[a,b,buff()],[notify(0),notify(.05,19,1)]+[notify(i/10,7) for i in range(1,5)]+[query(.4)],owners=[0,1,0])
 for bullet in (False,True):
  e=buff('plain',polarity='beneficial',target='all_allies',duration=.1,trigger=dict(timing=['event:full_reload'],condition=[]))
  if bullet:e['duration_bullets']=2
  add('direct-expired-unretired-refresh-'+str(bullet),[e,cleanse(trigger=dict(timing=['full_charge_hit'],condition=[]))],[notify(0),notify(.2),query(.2)])
 no_crit=buff('no crit',stat='crit_rate',fixed_value=-15,max_stack=1,polarity='beneficial',duration=-1,trigger=dict(timing=['battle_start'],condition=[]))
 e=buff('bullets',target='all_allies',duration_bullets=2,trigger=dict(timing=['event:full_reload'],condition=[]))
 c=add('cleanse-retains-independent-bullet-map',[no_crit,e,cleanse(target='self',trigger=dict(timing=['full_charge_fire'],condition=[]))],[notify(0),[0,4,0,0,0,-1,0,0],[.25,4,0,0,0,-1,0,0],notify(.3,11),[.5,4,0,0,0,-1,0,0],query(.5)],stack_bullet_reference=True)
 c['combat']['weapons']=[dict(enabled=True,capacity=100,interval=.25,reload=1,coefficient=100)]+[dict(enabled=False) for _ in range(4)]
 e=immune(duration_bullets=1,max_stack=3)
 c=add('charge-uses-representative-not-bullet-override',[copy.deepcopy(no_crit),e,buff(trigger=dict(timing=['full_charge_fire'],condition=[]))],[notify(0),notify(0),notify(0),[0,4,0,0,0,-1,0,0],[.25,4,0,0,0,-1,0,0],notify(.3)]+[notify(.4,11) for _ in range(4)]+[query(.4)],stack_bullet_reference=True)
 c['combat']['weapons']=[dict(enabled=True,capacity=100,interval=.25,reload=1,coefficient=100)]+[dict(enabled=False) for _ in range(4)]
 return rows
