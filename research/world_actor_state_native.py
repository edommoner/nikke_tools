"""Actual native predicate methods under the existing explicit query context."""
from impact_specs import ActorHandle,ActorKind
from world_actor_runtime import registry_for
from world_actor_pool_native import actor_bindings
from portable_enemy_specs import enemy_buff_plan
from calculator.buff_manager import _is_enemy
from effect_runtime import state

def before_finish(case,boss,manager,names,when):
 registry=registry_for(manager,boss);runtime=state(manager);queries=[]
 for who,kind,identity,generation,name in case.get('state_queries',[]):
  try:snapshot=registry.exact(ActorHandle(kind,identity,generation))
  except ValueError as e:queries.append(dict(status=3 if 'Stale' in str(e) else 2 if 'not spawned' in str(e) else 1));continue
  logical=registry.root(snapshot.handle) if kind==1 else snapshot
  if not hasattr(runtime,'enemy_query_stack'):runtime.enemy_query_stack=[]
  runtime.enemy_query_stack.append((logical.label,logical))
  try:present=manager._has_target_state(name);count=manager._target_stack(name)
  finally:runtime.enemy_query_stack.pop()
  queries.append(dict(status=0,kind=kind,identity=identity,generation=generation,alive=snapshot.alive,name=name,present=bool(present),stack=count,enemy_count=boss.enemy_count))
 allies=[];members=[]
 for ab in manager._active:
  if ab.effect.get('_boss_bound') or ab.effect.get('type')!='buff':continue
  # Native named-enemy selectors are valid before portable lowering exists.
  # Actual native recipients also classify new enemy carriers before a portable
  # lowering exists. This reads fields and a pure label predicate only; it
  # neither admits a GPU route nor resolves/queries a recipient again.
  raw_target=ab.effect.get('target','self')
  if enemy_buff_plan(ab.effect) is not None or isinstance(raw_target,str) and raw_target.startswith('enemies_with_buff:') or ab.target_chars is not None and any(_is_enemy(n) for n in ab.target_chars):members.append(bool(ab.target_chars));continue
  allies.append(dict(name=ab.effect.get('name',''),owner=names.index(ab.caster),recipients=None if ab.target_chars is None else [names.index(n) for n in ab.target_chars],stack=ab.stack,activated=ab.activated_at,end=ab.expires_at))
 return dict(queries=queries,allied_carriers=allies,enemy_memberships=members,context_restored=True)

def after_finish(boss):
 gone=set(boss.gone);out=[0]*4
 for slot,b in enumerate(actor_bindings(boss)):
  if int(b.kind)==5 and b.label in gone:out[slot//32]|=1<<(slot%32)
 return out
