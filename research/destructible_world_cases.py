"""Graph-controlled target lifetimes; amounts are authored resolved receipts."""
def binding(node='a',kind=2,identity=10,capacity=100,**kw):return dict(node=node,kind=kind,identity=identity,capacity=capacity,**kw)
def tick(t):return [0,0,0,0,0,t,0.,0.,0]
def hit(t=0.,slot=0,kind=2,identity=10,generation=1,amount=100.,credit=1.,outcome=2):return [1,slot,kind,identity,generation,t,amount,credit,outcome]
def select(t=0.,mask=28):return [2,0,0,0,0,t,0.,0.,mask]
def finish(t):return [3,0,0,0,0,t,0.,0.,0]
def fixtures():
 rows=[]
 def add(name,nodes,bindings,ops):rows.append(dict(name='destructible-world/'+name,nodes=nodes,bindings=bindings,ops=ops))
 add('timed-projectile',[dict(id='a',until=dict(time=1))],[binding()],[select(),select(.5),select(1),hit(1),finish(2)])
 add('delayed-shield',[dict(id='a',delay=.5,until=dict(time=.5))],[binding(kind=3)],[select(),select(.49),select(.5),hit(.6,kind=3,amount=30),select(1)])
 add('repeat-retires-live',[dict(id='a',after=['start','a'],repeat=3,until=dict(time=.2))],[binding()],[tick(0),tick(.2),hit(.2),hit(.2,generation=2,amount=25),tick(.4),select(.6)])
 add('all-targets-cleared',[dict(id='a',until=dict(targets_cleared=True)),dict(id='b',after=[dict(node='a',outcome='cleared')])],[binding(),binding(kind=3,identity=11),binding(node='b',kind=4,identity=12,capacity=2)],[hit(),select(.1),hit(.1,slot=1,kind=3,identity=11),select(.2),hit(.2,slot=2,kind=4,identity=12,amount=999,credit=.5)])
 add('same-time-reentry-defers-clear',[dict(id='a',after=['start','a'],repeat=2,until=dict(targets_cleared=True))],[binding()],[hit(),tick(0),select(0),tick(.01),hit(.01),hit(.01,generation=2),select(.02)])
 for clear in (False,True):
  for reverse in (False,True):
   nodes=[dict(id='a',until=dict(targets_cleared=True,time=1,after=[dict(node='b')])),dict(id='b',until=dict(time=1))]
   add('priority-'+str(clear)+'-'+str(reverse),nodes[::-1] if reverse else nodes,[binding(),binding(node='b',kind=3,identity=11)],[tick(0),hit(.5,amount=100 if clear else 10),select(1),finish(2)])
 add('follow-while-alive',[dict(id='a',until=dict(after=[dict(node='b',delay=.1)])),dict(id='b',until=dict(time=.5))],[binding(),binding(node='b',kind=3,identity=11)],[tick(0),select(.5),select(.59),select(.6)])
 add('finish-does-not-open-new-node',[dict(id='a',delay=1)],[binding()],[tick(0),finish(1)])
 add('finish-without-first-frame',[dict(id='a')],[binding()],[finish(0)])
 add('owner-is-descriptive',[dict(id='a',until=dict(time=.1)),dict(id='b',until=dict(time=1))],[binding(),binding(node='b',kind=3,identity=11,owner=[5,77,3])],[tick(0),select(.1),hit(.2,slot=1,kind=3,identity=11)])
 add('fractional-hit-shield-clear',[dict(id='a',until=dict(targets_cleared=True)),dict(id='b',after=['a'])],[binding(kind=4,capacity=2),binding(node='b',identity=11)],[hit(kind=4,credit=.25),hit(.1,kind=4,amount=0,credit=1.75),select(.1),select(.2)])
 add('high-slot128',[dict(id='a',until=dict(targets_cleared=True))],[binding(identity=1000+i) for i in range(128)],[select(),hit(.1,slot=127,identity=1127),select(.2)])
 add('unbound-clock-node',[dict(id='a',until=dict(time=.1)),dict(id='b',after=['a'])],[binding(node='b',kind=3)],[select(),select(.1),finish(.2)])
 nodes=[dict(id='a',after=['start','c'],repeat=2,until=dict(time=.1)),dict(id='b',after=['a'],repeat=2,until=dict(time=.1)),dict(id='c',after=['b'],repeat=2,until=dict(time=.1))]
 add('cycle-generations',nodes,[binding(node=n['id'],identity=10+i) for i,n in enumerate(nodes)],[select(i/10) for i in range(8)])
 add('expiry-epsilon',[dict(id='a',until=dict(time=1))],[binding()],[select(),select(1-2e-9),select(1-.5e-9)])
 add('spawn-epsilon',[dict(id='a',delay=1)],[binding()],[select(),select(1-2e-9),select(1-.5e-9)])
 for rational in (False,True):
  times=[0.];t=0.
  for i in range(1,31):t=i/60 if rational else t+1/60;times.append(t)
  add('frame-clock-'+str(rational),[dict(id='a',after=['start','a'],repeat=0,until=dict(time=.1))],[binding()],[select(t) for t in times])
 return rows
