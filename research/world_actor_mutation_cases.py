"""Authored named removal scopes and synchronous callback boundaries."""
import copy

def fixtures(state):
 fields=state.fields;base=copy.deepcopy(fields.fixtures()[0]);base.update(observe_named_state=True);rows=[]
 def buff(name='mark',target='all_enemies',**kw):return fields.pool.body.f.effect('received_dmg_pct' if 'enemies' in target or target in ('target','boss') or target.startswith('enemies_') else 'atk_pct',0,name=name,target=target,**kw)
 def remove(target='all_enemies',scope='target',timing='on_attack',name='mark',**kw):
  return dict(name='remove',source='스킬1',type='instant',stat='remove_named_buff',values={'10':0},target_effect=name,target=target,remove_scope=scope,trigger=dict(timing=[timing],condition=[]),**kw)
 def add(name,effects,owners=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners or [0]*len(effects));c['state_queries']=[(0,0,0,1,'mark'),(0,5,0,1,'mark'),(0,5,1,1,'mark')];rows.append(c);return c
 for target in ('boss','target','all_enemies','enemies_top_hp:1','enemies_highest_hp:2','enemies_lowest_hp:1','enemies_nearest:2','enemies_top_def:1','enemies_top_atk:2'):
  add('remove-wide-'+target,[buff(),remove(target)])
 for target in ('self','all_allies','allies_top_atk:1','allies_lowest_hp:1'):
  add('remove-ally-scope-'+target,[buff(target='all_allies'),buff(),remove(target)])
 for target in ('self','boss','target','all_enemies'):
  add('global-name-ignores-selector-'+target,[buff(target='all_allies'),buff(),remove(target,'global')])
 add('all-owners-same-name',[buff(),buff(),remove()],owners=[0,1,2])
 add('missing-name-no-effects',[buff(),remove(name='missing')])
 add('blank-name-preserved',[buff(name=''),remove(name='')])
 add('opaque-colon-unicode-name',[buff(name='a:b:名前'),remove(name='a:b:名前')])
 c=add('128-scope-no-mask-alias',[buff(),remove('enemies_top_atk:65')]);c['patterns'][0]['spec'].update(count=127,hp=1000000);c['state_queries']=[(0,5,i,1,'mark') for i in (0,63,64,65,126)]
 for scope in ('global','target'):
  c=add('empty-carrier-'+scope,[buff(duration=.3),remove(scope=scope)]);c['patterns'][0]['spec']['hp']=1300
  child=fields.pool.body.f.effect('atk_pct',2,name='expiry',target='self',duration=-1,max_stack=128,trigger=dict(timing=['event:state_end:mark'],condition=[]));c['effects'].append(child);c['owners'].append(0)
 for target in ('all_enemies','boss','target'):
  child=fields.pool.body.f.effect('atk_pct',2,name='after-all-removals',target='self',duration=-1,max_stack=128,trigger=dict(timing=['event:state_end:mark'],condition=['not_self_state:mark']))
  add('all-retire-before-callback-'+target,[buff(),remove(target),child])
 # Recursion re-applies the removed name;the newly created residents must survive.
 child=buff(name='mark',target='boss',duration=.25,trigger=dict(timing=['event:state_end:mark'],condition=[]))
 add('callback-recreates-same-name-after-scan',[buff(duration=.3),remove(),child])
 c=add('death-notice-removes-before-deferred-drop',[buff(),remove(timing='enemy_death')]);c['patterns'][0]['spec']['hp']=1300
 c=add('target-spawn-before-new-generation-drop',[buff(trigger=dict(timing=['on_attack'],condition=[])),remove(timing='enemy_death')]);c['patterns'][0].update(after=['start','wave'],repeat=0,until=dict(targets_cleared=True));c['patterns'][0]['spec']['hp']=1300
 return rows
