"""Authored fields/count/rank fixtures used unchanged by CUDA and Metal."""
import copy

def fixtures(pool):
 base=copy.deepcopy(pool.fixtures()[0]);base.update(observe_enemy_fields=True,duration=.5);rows=[]
 def wave(**kw):return dict(id='wave',kind='summon',spec=dict(count=3,hp=100000,**kw))
 def add(name,effects,patterns=None,owners=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners or [0]*len(effects),patterns=patterns or [wave()]);rows.append(c);return c
 def buff(stat,value,target='all_enemies',**kw):return pool.body.f.effect(stat,value,target=target,**kw)
 for stat,value in [('def_pct',-30),('def_caster_based_pct',-40),('received_dmg_pct',25)]:
  for target in ['boss','target','all_enemies']:
   c=add(stat+'-'+target,[buff(stat,value,target)]);c['environment']['allies'][0]['base_defense']=30
 for target in ['enemies_top_hp:2','enemies_highest_hp:2','enemies_lowest_hp:2','enemies_nearest:2','enemies_top_def:2','enemies_lowest_def:2','enemies_top_atk:2']:
  patterns=[wave(atk=114345)];patterns[0]['spec']['hp']=3000
  add('rank-'+target,[buff('received_dmg_pct',25,target)],patterns)
 c=add('fields-all128-resident-carriers',[buff('def_pct',-20)]);c['patterns'][0]['spec'].update(count=127,hp=1000000)
 c=add('stacked-field-refresh-per-target',[buff('received_dmg_pct',5,max_stack=3,trigger=dict(timing=['on_attack'],condition=[]))])
 c=add('same-name-independent-owners',[buff('received_dmg_pct',10,name='shared'),buff('received_dmg_pct',20,name='shared')],owners=[0,1])
 c=add('finite-field-expiry',[buff('received_dmg_pct',50,duration=.2)])
 p=wave();p.update(after=['start','wave'],until=dict(time=.15),repeat=0)
 add('stale-field-does-not-bind-reopened-adds',[buff('received_dmg_pct',25)],[p])
 add('repeated-field-new-generation',[buff('received_dmg_pct',5,max_stack=3,trigger=dict(timing=['on_attack'],condition=[]))],[p])
 add('child-buff-event-finishes-per-receiver',[buff('received_dmg_pct',5,name='field'),buff('atk_pct',2,target='all_allies',name='child',max_stack=128,trigger=dict(timing=['event:field'],condition=[]))])
 for timing,duration in [('battle_start',.3),('passive',-1),('on_attack',.15)]:
  for cmp in ('above','below'):
   c=add('enemy-count-'+timing+'-'+cmp,[buff('atk_pct',25,target='all_allies',duration=duration,trigger=dict(timing=[timing],condition=['enemy_count_'+cmp+':3']))]);c['patterns'][0]['spec']['hp']=1300
 for condition in ['target_is_boss','target_is_add']:
  c=add(condition+'-actual-aim-gate',[buff('atk_pct',25,target='all_allies',duration=.15,trigger=dict(timing=['on_attack'],condition=[condition]))]);c['patterns'][0]['spec']['hp']=1300
 c=add('count-body-not-part-colliders',[buff('atk_pct',25,target='all_allies',duration=-1,trigger=dict(timing=['passive'],condition=['enemy_count_above:2']))],[dict(id='parts',kind='parts',targets=[dict(name='part'+str(i),hp=1) for i in range(127)])])
 add('count-delayed-spawn-passive-gates',[buff('atk_pct',25,target='all_allies',duration=-1,trigger=dict(timing=['passive'],condition=['enemy_count_above:2']))],[dict(id='wave',kind='summon',delay=.2,until=dict(time=.15),spec=dict(count=2,hp=100000))])
 add('field-conditional-finite-latches',[buff('received_dmg_pct',25,duration=.5,trigger=dict(timing=['battle_start'],condition=['enemy_count_above:3']))],[dict(id='wave',kind='summon',until=dict(time=.15),spec=dict(count=2,hp=100000))])
 add('field-conditional-permanent-runtime',[buff('received_dmg_pct',25,duration=-1,trigger=dict(timing=['passive'],condition=['enemy_count_above:3']))],[dict(id='wave',kind='summon',until=dict(time=.15),spec=dict(count=2,hp=100000))])
 # World overlays remain in the same insertion order as character fields.
 c=add('world-field-sum-opening-order',[buff('received_dmg_pct',1e16,target='boss',name='positive'),buff('received_dmg_pct',-1e16,target='boss',name='negative')]);c['patterns']=[wave(),dict(id='world',kind='buff',enemy=dict(received_dmg_pct=1))]
 c=add('512-resident-capacity-with128-receivers',[buff('received_dmg_pct',i+1,name='field'+str(i)) for i in range(4)]);c['patterns'][0]['spec'].update(count=127,hp=1000000)
 for threshold in (1,4,5,-1):
  for comparison in ('above','below'):
   add('count-inclusive-'+comparison+'-'+str(threshold),[buff('atk_pct',25,target='all_allies',duration=.5,trigger=dict(timing=['battle_start'],condition=['enemy_count_'+comparison+':'+str(threshold)]))])
 c=add('field-on-dead-add-does-not-alias-body',[buff('received_dmg_pct',25)]);c['patterns'][0]['spec']['hp']=1300
 c=add('current-field-reaims-after-each-kill',[buff('received_dmg_pct',5,target='target',max_stack=3,trigger=dict(timing=['on_attack'],condition=[]))]);c['patterns'][0]['spec']['hp']=1300
 p=wave();p['spec']['hp']=1300;p.update(after=['start','wave'],until=dict(targets_cleared=True),repeat=0)
 add('fields-survive-as-stale-across-cleared-generations',[buff('received_dmg_pct',5,max_stack=3,trigger=dict(timing=['on_attack'],condition=[]))],[p])
 c=add('weapon-mode-and-independent-enemy-fields',[buff('received_dmg_pct',25),dict(name='mode',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=100,max_ammo=-1,fire_rate=10,fire_rate_max=10,charge=False,pellets=3,muzzles=1,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,target='self',duration=.2,trigger=dict(timing=['battle_start'],condition=[]))]);c['patterns'][0]['spec']['hp']=1300
 c=add('typed-query-exact-unknown-stale',[buff('received_dmg_pct',25)]);c['field_queries']=[(0,5,0,1),(0,0,0,1),(0,5,9,1),(0,5,0,2)]
 c=add('typed-query-unspawned-add',[buff('received_dmg_pct',25)],[dict(id='wave',kind='summon',delay=1,spec=dict(count=1,hp=3))]);c['field_queries']=[(0,5,0,1)]
 c=add('part-query-resolves-body-after-exact-generation',[buff('received_dmg_pct',25,target='boss')],[dict(id='parts',kind='parts',targets=[dict(name='part',hp=3)])]);c['field_queries']=[(0,1,0,1),(0,1,0,2)]
 return rows
