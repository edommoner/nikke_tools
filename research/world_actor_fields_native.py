"""Inspect actual native enemy recipients/queries;no GPU inputs or HP arithmetic."""
from impact_specs import ActorKind,ActorHandle
from world_actor_runtime import registry_for
from world_actor_pool_native import actor_bindings,pool_rows,bits
from portable_enemy_specs import enemy_buff_plan

def observe_before_finish(case,boss,manager,names,when):
 registry=registry_for(manager,boss);bindings=actor_bindings(boss);pools=pool_rows(boss);queries=[];carriers=[]
 for b,p in zip(bindings,pools):
  if p[0]==0:queries.append([2]+[0]*11);continue
  snapshot=registry.exact(ActorHandle(b.kind,b.identity,p[0]));label='__enemy__' if int(b.kind)==1 else b.label
  actual=manager.get_buffs(names[0],label,when)
  queries.append([0,int(b.kind),b.identity,snapshot.handle.generation,int(snapshot.alive),boss.enemy_count,*bits(actual.get('enemy_def_down_pct',0)),*bits(actual.get('enemy_def_down_flat',0)),*bits(actual.get('received_dmg',0))])
 for ab in manager._active:
  if ab.effect.get('_boss_bound') or enemy_buff_plan(ab.effect) is None:continue
  key=getattr(ab,'enemy_recipient_key',None)
  if key is not None:handles=[b.actor for b in key.bindings]
  else:handles=[registry.view(ActorKind.BODY if label=='__enemy__' else ActorKind.ADD,label).handle for label in ab.target_chars or ()]
  assert len(handles)==1 or case.get('allow_shared_enemy_fields')
  h=handles[0]
  row=dict(name=ab.effect['name'],owner=names.index(ab.caster),actor=[int(h.kind),h.identity,h.generation],stack=ab.stack,activated=ab.activated_at,end=ab.expires_at)
  if len(handles)>1:row.pop('actor');row['actors']=[[int(x.kind),x.identity,x.generation] for x in handles]
  carriers.append(row)
 explicit=[]
 for who,kind,identity,generation in case.get('field_queries',[]):
  try:snap=registry.exact(ActorHandle(kind,identity,generation))
  except ValueError as e:explicit.append([3 if 'Stale' in str(e) else 2 if 'not spawned' in str(e) else 1]+[0]*15);continue
  label='__enemy__' if kind==1 else snap.label;actual=manager.get_buffs(names[who],label,when)
  explicit.append([0,kind,identity,generation,int(snap.alive),boss.enemy_count,*bits(actual.get('enemy_def_down_pct',0)),*bits(actual.get('enemy_def_down_flat',0)),*bits(actual.get('received_dmg',0)),0,0,0,0])
 answer=dict(queries=queries,carriers=carriers,explicit_queries=explicit,owned_snapshots=0)
 if case.get('allow_shared_enemy_fields'):
  answer['recipient_memberships']=[]
  for ab in manager._active:
   if ab.effect.get('_boss_bound') or enemy_buff_plan(ab.effect) is None:continue
   key=getattr(ab,'enemy_recipient_key',None);assert key is not None
   answer['recipient_memberships'].append([[int(x.actor.kind),x.actor.identity,x.actor.generation] for x in key.bindings if x.label in (ab.target_chars or [])])
 return answer
