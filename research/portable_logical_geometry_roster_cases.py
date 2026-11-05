"""Original Nihilister two-enemy consumer on literal logical ADD geometry."""
import copy
from portable_original_identity_inventory import profile_bodies

def fixtures():
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    original=next(b for n,s,b in profile_bodies() if (n,s)==('니힐리스타',0));rows=[]
    for label,duration,outside,part,rectangle in [('two-enemies',3,False,False,False),('one-outside',3,True,False,False),('part-not-enemy',3,True,True,False),('rotated-rectangle',3,False,False,True),('two-enemies-long',30,False,False,False)]:
        body=copy.deepcopy(original);body.update(duration=duration,seed=4401)
        patterns=[dict(id='nihilister-wave',kind='summon',spec=dict(count=1,hp=1e30))]
        if part:patterns.append(dict(id='real-parts',kind='parts',targets=[dict(name='real-part',hp=1e30,x=0.,y=0.,r=100.,z=5.)]))
        scalar=copy.deepcopy(patterns)
        for pattern in scalar:
            if pattern['kind']=='parts':
                for target in pattern['targets']:
                    for key in ('x','y','r','z'):target.pop(key)
                    target['reach']=1
        body['enemy'].update(has_parts=False,patterns=scalar)
        label_add=next(b.label for b in bindings(validate(patterns,coord=True)) if int(b.kind)==5)
        shape=dict(x=100000. if outside else 0.,y=0.,r=1. if outside else 100.,z=1.)
        if rectangle:shape=dict(x=0.,y=0.,w=200.,h=200.,rot=37.,z=1.)
        rows.append(dict(name='logical-actor-rosters/Nihilister/'+label,body=body,patterns=patterns,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),logical_geometry=[dict(label=label_add,shape=shape)],
            contract=dict(scenario=label,owner='니힐리스타',definitions=70,threshold=2,part=part,outside=outside,rectangle=rectangle,duration=duration,child='버닝 샷 3')))
    return rows
