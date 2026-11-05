"""Read actual native clock/container state; no timer or damage reconstruction."""
from world_actor_pool_native import actor_bindings
def before_finish(boss,manager,names):
 lookup={b.label:i for i,b in enumerate(actor_bindings(boss))}
 effects={id(e):(e,owner) for e,owner in manager._effects};timers=[];carriers=[]
 for identity,(owner,due,expiry) in manager._dot_timers.items():
  effect,_=effects[identity];row=effect['_portable_observer_row']
  timers.append(dict(row=row,due=due,expiry=expiry))
 for ab in manager._active:
  effect=ab.effect
  if effect.get('type')!='damage' or not effect.get('tick_interval'):continue
  members=[lookup[label] for label in ab.target_chars or [] if label in lookup]
  carriers.append(dict(row=effect['_portable_observer_row'],stack=ab.stack,activated=ab.activated_at,end=ab.expires_at,recipients=members))
 return dict(timers=timers,carriers=carriers)
