"""State-operation inputs. Not a battle replay and not GPU admission evidence."""
NONE=0xffffffff
# op,logical,policy-or-stat,name,owner,value,stack,hp

def pool(slot=0,stat=81,name=1,owner=0,cap=10000):return [0,slot,stat,name,owner,cap,1,100.]
def rate(slot=1,value=50.,name=NONE,owner=0,present=True,named=False,stack=1,lost=False,hp=100.):return [1,slot,int(present)|(int(named)<<1)|(int(lost)<<2)|(int(stack!=1)<<3),name,owner,value,stack,hp]
def hit(value=900.,owner=0):return [2,owner,0,0,0,value,0,0]
def take(name=1,split=0.):return [3,0,0,name,0,split,0,0]
def remove(slot=0):return [4,slot,0,0,0,0.,0,0]
def query(slot=0):return [5,slot,0,0,0,0.,0,0]
def fixtures():
 rows=[]
 def add(name,ops,capacity=32,reject=False):rows.append(dict(name='damage-accum-core/'+name,ops=ops,capacity=capacity,reject=reject))
 add('dealt',[pool(),hit(),take()])
 add('received',[pool(stat=82),hit(owner=4),take()])
 add('other-caster',[pool(),hit(owner=4),take()])
 add('absent-rate',[pool(),rate(present=False),query(),hit(),take()])
 add('explicit-zero',[pool(),rate(value=0.),query(),hit(),take()])
 add('named25',[pool(),rate(value=25.,name=1,named=True),query(),hit(),take()])
 add('base50-named25',[pool(),rate(),rate(slot=2,value=25.,name=1,named=True),query(),hit(),take()])
 add('wrong-name-and-owner',[pool(),rate(value=25.,name=2,named=True),rate(slot=2,owner=1),query(),hit(),take()])
 add('negative-rate',[pool(),rate(value=-50.),hit(),take()])
 add('negative-cap',[pool(cap=-1000.),hit(),take()])
 add('zero-cap',[pool(cap=0.),hit(),take()])
 add('clamped',[pool(cap=500.),hit(),hit(),take(),hit(),take()])
 add('epsilon-inside',[pool(cap=900.+.5e-9),hit(),take()])
 add('epsilon-outside',[pool(cap=900.+2e-9),hit(),take()])
 add('archived',[pool(),hit(),remove(),take(),take()])
 add('refresh-clears',[pool(),hit(),pool(),remove(),take()])
 add('dealt-before-received',[pool(slot=0,stat=82,name=1,cap=500.),pool(slot=1,name=2,cap=500.),hit(),take(2),take(1)])
 add('first-active-done-shadows',[pool(),pool(slot=1,stat=82,owner=1),hit(),take(),take()])
 add('last-archive',[pool(),pool(slot=1,stat=82,owner=1),hit(),hit(owner=1),remove(),remove(1),take()])
 add('first-active-reverse-stat',[pool(stat=82),pool(slot=1,owner=1),hit(),take(),take()])
 add('lost-hp41',[pool(),rate(value=1.,lost=True,stack=5,hp=59.),query(),hit(),take()])
 add('live-lost-hp',[pool(),rate(value=1.,lost=True,hp=59.),hit(),[6,0,0,0,0,100.,0,0],query(),hit(),take()])
 add('stacked',[pool(),rate(value=100.,stack=2),query(),hit(),take()])
 add('ordered-cancellation',[pool(),rate(value=1e16),rate(slot=2,value=-1e16),rate(slot=3,value=1.),query(),hit(),take()])
 add('separate-rate-groups',[pool(),rate(value=1e16),rate(slot=2,value=1.,name=1,named=True),rate(slot=3,value=-1e16),query(),hit(),take()])
 add('release-feeds-other',[pool(),pool(slot=1,stat=82,name=2),hit(),take(),hit(),take(2)])
 add('split-truncation',[pool(),hit(),remove(),take(split=25.19)])
 add('positive-truncates-zero',[pool(),hit(value=.4),take()])
 add('negative-split-packet',[pool(),hit(),take(split=-150.)])
 add('zero-negative-credit',[pool(),hit(value=0.),hit(value=-900.),take()])
 add('missing-name-ledger',[take(22),take(22)])
 add('empty-pool-name',[pool(name=NONE),hit(),remove(),take(1)])
 add('rate-retired',[pool(),rate(),remove(1),query(),hit(),take()])
 add('slot-reused-order',[pool(),pool(slot=1,stat=82,owner=1),hit(),remove(),pool(slot=0,owner=0),hit(),take()])
 add('invalid-rate-policy',[pool(),[1,1,16,NONE,0,50.,1,100.]],reject=True)
 add('invalid-rate-owner',[pool(),rate(owner=5)],reject=True)
 add('archive-capacity-exhausted',[pool()],capacity=1,reject=True)
 add('unknown-operation',[[99,0,0,0,0,0.,0,0]],reject=True)
 add('nan-credit',[pool(),hit(float('nan'))],reject=True)
 add('infinite-rate',[pool(),rate(value=float('inf')),hit()],reject=True)
 add('emission-int64-overflow',[pool(cap=1e30),hit(value=1e25),take()],reject=True)
 return rows
