"""Authored source-lifecycle operations, not CPU-derived target lists."""
import copy

def fixtures():
    targets=[dict(name='near',hp=100,x=0,y=0,r=2,z=2),dict(name='far',hp=100,x=30,y=0,w=10,h=10,rotation=45,z=1)]
    base=dict(name='coordinate-scene/base',patterns=[dict(id='parts',kind='parts',targets=targets),dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=100,x=0,y=0,r=1,z=3)])])
    rows=[]
    def add(label):c=copy.deepcopy(base);c['name']='coordinate-scene/'+label;rows.append(c);return c
    add('base')
    add('reverse-depth')['patterns'][0]['targets'][1]['z']=4
    c=add('same-depth-later-birth')
    for p in c['patterns']:
        for t in p['targets']:t['z']=0
    c=copy.deepcopy(c);c['name']='coordinate-scene/reverse-pattern-order';c['patterns'].reverse();rows.append(c)
    c=add('unbreakable')
    for p in c['patterns']:
        for t in p['targets']:t['hp']=0
    c=add('negative-subnormal-depth');c['patterns'][0]['targets'][0].update(x=-0.,y=-0.,z=-5e-324);c['patterns'][0]['targets'][1]['z']=-1e300;c['patterns'][1]['targets'][0]['z']=0.
    c=add('signed-zero-depth')
    for p in c['patterns']:
        for i,t in enumerate(p['targets']):t['z']=-0. if i==0 else 0.
    c=add('capacity127');c['patterns'][0]['targets']=[dict(name='p'+str(i),hp=100,x=i,y=-i,r=2,z=0) for i in range(64)];c['patterns'][1]['targets']=[dict(name='i'+str(i),hp=100,x=i,y=0,w=2,h=3,rotation=-45,z=0) for i in range(63)]
    rows.append(dict(name='coordinate-scene/empty',patterns=[dict(id='idle',kind='idle')]))
    rows.append(dict(name='coordinate-scene/pattern31',patterns=[dict(id='p'+str(i),kind='parts',targets=[dict(name='t'+str(i),hp=100,x=i,y=0,r=2,z=0)]) for i in range(32)]))
    for c in rows:
        count=sum(len(p.get('targets',[])) for p in c['patterns']);last=len(c['patterns'])-1
        ops=[('open',0.,0,0)]
        if last:ops.append(('open',0.,last,0))
        ops.append(('capture',0.,0,0))
        if count:ops.extend([('hit',.1,0,100),('hit',.1,0,100),('capture',.1,0,0)])
        ops.extend([('close',.2,0,0),('open',.3,0,0),('capture',.3,0,0)]);c['commands']=ops
    return rows
