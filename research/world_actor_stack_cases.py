"""Typed stack scopes preserve independent and shared native carrier semantics."""
import copy

def fixtures(status):
 base=copy.deepcopy(status.fixtures()[0]);base['state_queries']=[(0,0,0,1,'seed'),(0,5,0,1,'seed'),(0,5,64,1,'seed'),(0,5,126,1,'seed')];rows=[];e=status.recipient.state.fields.pool.body.f.effect
 def seed(target='all_enemies',timing='battle_start',polarity='harmful',duration=2,max_stack=5):return e('received_dmg_pct' if target!='all_allies' else 'atk_pct',5,name='seed',target=target,polarity=polarity,duration=duration,max_stack=max_stack,trigger=dict(timing=[timing],condition=[]))
 def op(stat,value=1,target='all_enemies',name='seed',**kw):
  out=dict(name='operation',source='스킬1',type='buff' if stat=='buff_max_stack_add' else 'instant',stat=stat,fixed_value=value,target=target,max_trigger=1,trigger=dict(timing=['on_attack'],condition=[]))
  if name is not None:out['target_effect']=name
  out.update(kw);return out
 def add(name,effects,owners=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners or [0]*len(effects));rows.append(c);return c
 for stat in ('debuff_stack_add','debuff_stack_remove'):
  for target in ('boss','target','all_enemies','enemies_top_atk:65'):
   add('independent-'+stat+'-'+target,[seed(),op(stat,1,target)])
  for value in (0.,-0.,.5,-.5,3.9,-3.9,1e308,-1e308):
   add('stack-delta-'+stat+'-'+repr(value),[seed(),op(stat,value)])
  for named in ('seed',None):
   template=seed(timing='event:full_reload');init=op('buff_stack_init',3,target='all_enemies',trigger=dict(timing=['battle_start'],condition=[]))
   add('shared-once-'+stat+'-'+str(named),[template,init,op(stat,1,target='enemies_top_atk:65',name=named)])
 for target in ('all_enemies','enemies_top_atk:65'):
  for stat in ('debuff_stack_add','debuff_stack_remove'):
   add('independent-stack-immunity-'+target+'-'+stat,[seed(),e('stack_change_immune',0,name='immune',target=target),op(stat,1)])
 template=seed(timing='event:full_reload');init=op('buff_stack_init',3,trigger=dict(timing=['battle_start'],condition=[]))
 add('shared-partial-immunity-does-not-split-stack',[template,init,e('stack_change_immune',0,name='immune',target='enemies_top_atk:65'),op('debuff_stack_add',1)])
 for stat in ('buff_stack_add','buff_stack_remove'):
  add('own-stack-'+stat,[seed('all_allies',polarity='beneficial'),op(stat,2,target='self')],owners=[1,0])
  add('own-stack-immune-'+stat,[seed('all_allies',polarity='beneficial'),e('stack_change_immune',0,name='immune',target='self'),op(stat,2,target='self')],owners=[1,0,0])
 for target in ('self','all_allies','all_enemies'):
  add('maximum-shared-ally-'+target,[seed('all_allies',polarity='beneficial'),op('buff_max_stack_add',2,target=target)],owners=[1,0])
 add('named-control-can-change-beneficial-enemy-field',[seed(polarity='beneficial'),op('debuff_stack_remove',1)])
 add('unnamed-control-ignores-beneficial-enemy-field',[seed(polarity='beneficial'),op('debuff_stack_remove',1,name=None)])
 add('unnamed-control-ignores-irremovable-field',[seed(polarity='harmful_irremovable'),op('debuff_stack_remove',1,name=None)])
 add('named-zero-stack-remains-present',[seed(),op('debuff_stack_remove',10)])
 add('unnamed-stack-floor-one',[seed(),op('debuff_stack_remove',10,name=None)])
 c=add('own-positive-refreshes-duration-and-notifies-after-change',[seed('all_allies',polarity='beneficial',duration=.3),op('buff_stack_add',2,target='self',trigger=dict(timing=['enemy_death'],condition=[])),e('atk_pct',5,name='reached',target='all_allies',trigger=dict(timing=['stack_reach:seed:3'],condition=[]))],owners=[1,0,1]);c['patterns'][0]['spec'].update(count=3,hp=1300);c['base_atk']=[1000,0,0,0,0];c['duration']=.5;c['state_queries']=[(0,0,0,1,'seed')]
 c=add('stale-generations-are-not-stack-mutated',[seed(timing='on_attack'),op('debuff_stack_add',1,trigger=dict(timing=['event:target_spawn'],condition=[]),max_trigger=10)]);c['patterns'][0]['spec'].update(count=3,hp=100000);c['patterns'][0].update(after=['start','wave'],until=dict(time=.1),repeat=0,emit=['event:target_spawn']);c['duration']=.25;c['state_queries']=[(0,0,0,1,'seed'),(0,5,0,3,'seed')]
 for stat,value,named in [('debuff_stack_add',3.9,'seed'),('debuff_stack_remove',9.,'seed'),('debuff_stack_add',3.,None)]:
  add('unlimited-'+stat+'-'+str(named),[seed(max_stack=-1),op(stat,value,name=named)])
 template=seed(timing='event:full_reload');init=op('buff_stack_init',3,trigger=dict(timing=['battle_start'],condition=[]))
 add('shared-delta-from-owned-stack-reference',[template,init,op('debuff_stack_add',1,target='enemies_top_atk:65',scaling='stack_count',scaling_ref='seed')])
 add('missing-stack-reference-keeps-literal-delta',[seed(),op('debuff_stack_add',1,scaling='stack_count',scaling_ref='missing')])
 add('unlimited-last-exact31bit-stack',[seed(max_stack=-1),op('debuff_stack_add',2147483646)])
 return rows
