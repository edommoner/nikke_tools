"""Authored state contracts, not invented in-game projectile/shield mechanics."""
NONE=0xffffffff
# op,slot,kind,id,generation,time,value,expiry-or-credit,ownerKind,ownerId,ownerGen,policy

def spawn(slot=0,kind=2,identity=10,generation=1,t=0.,value=100.,expires=-1.,owner=None):
 return [0,slot,kind,identity,generation,t,value,expires,*(owner or (NONE,0,0)),0]
def hit(slot=0,kind=2,identity=10,generation=1,t=0.,amount=30.,credit=1.,outcome=2):return [1,slot,kind,identity,generation,t,amount,credit,NONE,0,0,outcome]
def retire(slot=0,kind=2,identity=10,generation=1,t=0.):return [2,slot,kind,identity,generation,t,0.,0.,NONE,0,0,0]
def select(kinds=4,t=0.):return [3,0,0,0,0,t,0.,0.,NONE,0,0,kinds]
def fixtures():
 rows=[]
 def add(name,ops,capacity=128,reject=False):rows.append(dict(name='destructible-target-core/'+name,ops=ops,capacity=capacity,reject=reject))
 add('projectile-cap',[spawn(),hit(),hit(amount=90.),hit(),select()])
 add('hp-shield-cap',[spawn(kind=3),hit(kind=3,amount=125.),select(8)])
 add('hit-shield-fractional-credit',[spawn(kind=4,value=2.),hit(kind=4,amount=999.,credit=.25),hit(kind=4,amount=0.,credit=1.75),select(16)])
 add('zero-packet-credit',[spawn(kind=4,value=1),hit(kind=4,amount=0,credit=1)])
 add('blocked-hp-no-consumption',[spawn(kind=3),hit(kind=3,amount=0,outcome=1),select(8)])
 add('blocked-hit-explicit-credit',[spawn(kind=4,value=1),hit(kind=4,amount=0,outcome=1)])
 add('miss-no-consumption',[spawn(),hit(amount=0,credit=0,outcome=0)])
 add('zero-credit-damage',[spawn(),hit(amount=10,credit=0)])
 add('zero-damage-hit-shield',[spawn(kind=4,value=2),hit(kind=4,amount=0,credit=0),hit(kind=4,credit=1)])
 add('expiry-exclusive-boundary',[spawn(expires=1.),select(t=.999),select(t=1.),hit(t=1.)])
 add('retired-target-not-selected',[spawn(),retire(),hit(),select()])
 add('stale-generation-after-respawn',[spawn(),retire(),spawn(generation=2),hit(),hit(generation=2),select()])
 add('stale-retirement',[spawn(),retire(),spawn(generation=2),retire(),select()])
 add('foreign-identity-receipt',[spawn(),hit(identity=11),hit(kind=3),select()])
 add('two-shields-one-owner',[spawn(kind=3,owner=(0,0,1)),spawn(slot=1,kind=4,identity=11,value=2,owner=(0,0,1)),hit(kind=3,amount=120),select(24)])
 add('add-owner-generation',[spawn(owner=(5,77,3)),hit(),select()])
 add('all-projectiles-excludes-shields',[spawn(),spawn(slot=1,kind=3,identity=11),spawn(slot=2,kind=4,identity=12,value=3),select(4),select(24),select(28)])
 add('high-slot-bitmap',[spawn(slot=127),spawn(slot=64,identity=11),spawn(slot=31,identity=12),select()])
 add('fractional-hp',[spawn(value=.5),hit(amount=.25),hit(amount=.5)])
 add('binary64-large-hp',[spawn(value=2**53+2),hit(amount=2**53),hit(amount=2)])
 add('last-finite-capacity',[spawn(value=1e30),hit(amount=1e30)])
 add('expiry-respawn-same-time',[spawn(expires=1),spawn(generation=2,t=1,expires=2),hit(t=1)])
 add('exact-capacity-one',[spawn(),hit(amount=100),spawn(generation=2)],capacity=1)
 add('independent-generation-slots',[spawn(),spawn(slot=1,identity=11),retire(),spawn(generation=2),select()])
 add('invalid-actor-kind',[spawn(kind=1)],reject=True)
 add('duplicate-live-spawn',[spawn(),spawn()],reject=True)
 add('wrong-initial-generation',[spawn(generation=2)],reject=True)
 add('generation-skip',[spawn(),retire(),spawn(generation=3)],reject=True)
 add('slot-kind-rebinding',[spawn(),retire(),spawn(kind=3,generation=2)],reject=True)
 add('duplicate-identity',[spawn(),spawn(slot=1)],reject=True)
 add('slot-overflow',[spawn(slot=128)],reject=True)
 add('fractional-hit-cap',[spawn(kind=4,value=1.5)],reject=True)
 add('hit-cap-overflow',[spawn(kind=4,value=2**31)],reject=True)
 add('nonfinite-cap',[spawn(value=float('inf'))],reject=True)
 add('nonfinite-credit',[spawn(),hit(credit=float('nan'))],reject=True)
 add('negative-clock',[spawn(t=-1)],reject=True)
 add('clock-reversal',[spawn(t=1),hit(t=.5)],reject=True)
 add('expired-at-spawn',[spawn(expires=0)],reject=True)
 add('unknown-owner',[spawn(owner=(2,1,1))],reject=True)
 add('unknown-selection',[spawn(),select(32)],reject=True)
 add('blocked-damage',[spawn(),hit(amount=1,outcome=1)],reject=True)
 add('miss-credit',[spawn(),hit(amount=0,outcome=0)],reject=True)
 return rows
