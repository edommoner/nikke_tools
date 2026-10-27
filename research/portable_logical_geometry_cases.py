"""Original Belorta roster with literal ADD colliders, no authored hit schedules."""
import copy
from portable_original_identity_inventory import profile_bodies

def fixtures():
    body=copy.deepcopy(next(b for n,s,b in profile_bodies() if (n,s)==('벨로타',0)));rows=[]
    for label,count,duration,hp,part,outside in [('four-live',3,3,1e30,False,False),('three-enemies',2,3,1e30,False,False),('one-outside',3,3,1e30,False,True),('part-not-enemy',2,3,1e30,True,False),('retirement',3,3,1.,False,False),('four-live-long',3,30,1e30,False,False)]:
        b=copy.deepcopy(body);b.update(duration=duration,seed=4301);patterns=[dict(id='logical-wave',kind='summon',spec=dict(count=count,hp=hp))]
        if label=='retirement':patterns[0]['delay']=1.51
        if part:patterns.append(dict(id='real-parts',kind='parts',targets=[dict(name='real-part',hp=1e30,x=0.,y=0.,r=100.,z=5.)]))
        scalar=copy.deepcopy(patterns)
        for pattern in scalar:
            if pattern['kind']=='parts':
                for target in pattern['targets']:
                    for key in ('x','y','r','z'):target.pop(key)
                    target['reach']=1
        b['enemy'].update(has_parts=False,patterns=scalar)
        from world_actor_specs import bindings
        from calculator.boss_pattern import validate
        labels=[r.label for r in bindings(validate(patterns,coord=True)) if int(r.kind)==5]
        spec=[dict(label=n,shape=dict(x=100000. if outside and i==count-1 else 0.,y=0.,r=1. if outside and i==count-1 else 100.,z=float(i+1))) for i,n in enumerate(labels)]
        rows.append(dict(name='logical-actor-geometry/Belorta/'+label,body=b,patterns=patterns,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),logical_geometry=spec,contract=dict(scenario=label,count=count,duration=duration,threshold=4,part=part,outside=outside)))
    return rows
