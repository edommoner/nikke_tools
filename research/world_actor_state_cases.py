"""Authored named predicates;GPU chooses recipients,counts,lifetimes and context."""
import copy

def fixtures(fields):
 base=copy.deepcopy(fields.fixtures()[0]);base.update(observe_named_state=True);rows=[]
 def buff(stat,value,name,target='all_allies',timing='battle_start',condition=(),duration=-1,**kw):return fields.pool.body.f.effect(stat,value,name=name,target=target,duration=duration,trigger=dict(timing=[timing],condition=list(condition)),**kw)
 def marker(target='target',name='mark',timing='battle_start',duration=-1,max_stack=1):return buff('received_dmg_pct',0,name,target,timing,duration=duration,max_stack=max_stack)
 def add(name,effects,owners=None,patterns=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners or [0]*len(effects));
  if patterns is not None:c['patterns']=patterns
  c['state_queries']=[(0,0,0,1,'mark'),(0,5,0,1,'mark')];rows.append(c);return c
 for target in ('boss','target'):
  for cond in ('target_state:mark','not_target_state:mark'):
   for timing,duration in [('battle_start',.3),('on_attack',.15),('passive',-1)]:
    add(target+'-'+cond+'-'+timing,[marker(target),buff('atk_pct',20,'conditional',timing=timing,condition=[cond],duration=duration)])
 for target in ('boss','target','all_enemies'):
  add('enemy-runtime-recipient-state-'+target,[marker(target),buff('received_dmg_pct',25,'dependent',target='all_enemies',timing='passive',condition=['target_state:mark'])])
 add('fanout-parent-gate-once-before-receivers',[marker(),buff('received_dmg_pct',25,'dependent',target='all_enemies',timing='on_attack',condition=['target_state:mark'],duration=.3)])
 for threshold in (0,1,2,3,2147483647):
  add('target-stack-threshold-'+str(threshold),[marker(timing='on_attack',max_stack=3),buff('atk_pct',20,'conditional',timing='on_attack',condition=['target_stack_above:mark:'+str(threshold)],duration=.15)])
 add('target-stack-max-across-owners-not-sum',[marker(),marker(),buff('atk_pct',20,'conditional',condition=['target_stack_above:mark:2'],duration=.3)],owners=[0,1,2])
 add('missing-state-zero-stack-passes',[buff('atk_pct',20,'conditional',condition=['target_stack_above:missing:0'],duration=.3)])['state_queries']=[(0,0,0,1,'missing'),(0,5,0,1,'missing')]
 for name in ('a:b: :名前',' mark ',''):
  c=add('opaque-target-name-'+repr(name),[marker(name=name),buff('atk_pct',20,'conditional',condition=['target_stack_above:'+name+':1'],duration=.3)]);c['state_queries']=[(0,0,0,1,name),(0,5,0,1,name)]
 for condition in ('self_state:mark','not_self_state:mark','self_stack_above:mark:1'):
  add('enemy-field-'+condition,[marker(),buff('atk_pct',20,'conditional',condition=[condition],duration=.3)])
 for condition in ('self_state:ally','not_self_state:ally','self_stack_above:ally:1'):
  add('ally-field-other-owner-'+condition,[buff('received_dmg_pct',0,'ally',target='all_allies'),buff('atk_pct',20,'conditional',condition=[condition],duration=.3)],owners=[1,0])
 c=add('death-notice-before-self-stack-drop',[marker(),buff('atk_pct',10,'death-child',timing='enemy_death',condition=['self_stack_above:mark:1'],duration=.3,max_stack=128)]);c['patterns'][0]['spec']['hp']=1300
 c=add('death-cleared-and-fresh-generation',[marker(timing='on_attack'),buff('atk_pct',10,'conditional',timing='on_attack',condition=['target_state:mark'],duration=.15)]);c['patterns'][0].update(after=['start','wave'],repeat=0,until=dict(targets_cleared=True));c['patterns'][0]['spec']['hp']=1300
 c=add('empty-enemy-carrier-still-emits-state-end',[marker(target='all_enemies',duration=.2),buff('atk_pct',2,'expiry-child',timing='event:state_end:mark',max_stack=128)]);c['patterns'][0]['spec']['hp']=1300
 c=add('same-frame-aim-changes-after-kill',[marker(),buff('atk_pct',20,'conditional',timing='on_attack',condition=['target_state:mark'],duration=.15)],owners=[0,1]);c['patterns'][0]['spec']['hp']=1300
 c=add('named-child-does-not-inherit-field-recipient',[marker('boss'),buff('atk_pct',20,'conditional',timing='event:mark',condition=['target_state:mark'],duration=.15)]);c['patterns'][0]['spec']['hp']=1300
 c=add('direct-incoming-and-body-query-have-different-context',[marker(),buff('invincible',0,'guard',timing='passive',condition=['target_state:mark']),buff('atk_pct',20,'conditional',timing='passive',condition=['target_state:mark'])]);c['patterns']+=[dict(id='attack',kind='attack',spec=dict(atk=200,coeff=100,target='all',hits=4,interval=.1))];c['patterns'][0]['spec']['hp']=1300
 for target in ('boss','target'):
  c=add('dictionary-ammo-context-'+target,[marker(target),buff('max_ammo_pct',50,'capacity',timing='passive',condition=['target_state:mark'])]);c['duration']=.8
  for w in c['combat']['weapons']:w.update(capacity=2,reload=.2)
  c=add('dictionary-infinite-ammo-context-'+target,[marker(target),buff('infinite_ammo',0,'infinite',timing='passive',condition=['target_state:mark'])]);c['duration']=.8
  for w in c['combat']['weapons']:w.update(capacity=2,reload=.2)
 c=add('128-typed-predicates-canonical-keys',[marker(target='all_enemies'),buff('received_dmg_pct',5,'dependent',target='all_enemies',timing='passive',condition=['target_state:mark'])]);c['patterns'][0]['spec'].update(count=127,hp=1000000);c['state_queries']=[(0,5,126,1,'mark'),(0,5,127,1,'mark'),(0,5,0,2,'mark')]
 c=add('typed-query-never-aliases-unspawned-body',[marker('boss')]);c['patterns'][0]['delay']=1;c['state_queries']=[(0,5,0,1,'mark'),(0,0,0,1,'mark')]
 c=add('typed-part-query-root-after-exact-generation',[marker('boss')],patterns=[dict(id='parts',kind='parts',targets=[dict(name='part',hp=3)])]);c['state_queries']=[(0,1,0,1,'mark'),(0,1,0,2,'mark')]
 for condition in ('self_state:mode','not_self_state:mode','self_state:무기 변경','self_stack_above:mode:1'):
  mode=dict(name='mode',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=100,max_ammo=-1,fire_rate=10,fire_rate_max=10,charge=False,pellets=1,muzzles=1,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,target='self',duration=.2,trigger=dict(timing=['battle_start'],condition=[]))
  add('weapon-mode-'+condition,[marker('boss',name='mode'),mode,buff('atk_pct',20,'conditional',timing='on_attack',condition=[condition],duration=.15)],owners=[1,0,0])
 return rows
