"""Original Anne roster and source-scheduled finite ADD healing declarations."""
import copy
from portable_original_identity_inventory import profile_bodies

def fixtures():
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    original=next(b for n,s,b in profile_bodies() if (n,s)==('앤 : 미라클 페어리',0));rows=[]
    for label,level,amount,hp,renew in [('level10',10,1000.,1e9,False),('level1',1,1000.,1e9,False),('capped',10,1e12,1e9,False),('dead',10,1000.,1.,False),('renewal',10,1000.,1e9,True),('fractional-death',10,1000.,1e9,False)]:
        body=copy.deepcopy(original);body.update(duration=36 if renew else 56,seed=4501)
        body['profile']['chars']['앤 : 미라클 페어리']['skill_levels']['2']=level
        wave=dict(id='healing-wave',kind='summon',spec=dict(count=2,hp=hp))
        if renew:wave.update(after=['start','healing-wave'],until=dict(time=26),repeat=2)
        times=[1.,25.,26.,35.] if renew else [1.,25.,35.,55.]
        waves=[wave]
        if label=='fractional-death':waves=[dict(id='healing-low',kind='summon',spec=dict(count=1,hp=14000000.)),dict(id='healing-high',kind='summon',spec=dict(count=1,hp=1e9))]
        patterns=[*waves,*[dict(id='enemy-heal-'+str(i),kind='idle',delay=t) for i,t in enumerate(times)]]
        body['enemy'].update(has_parts=False,patterns=copy.deepcopy(patterns))
        labels=[b.label for b in bindings(validate(patterns,coord=True)) if int(b.kind)==5]
        rows.append(dict(name='enemy-healing/Anne/'+label,body=body,patterns=patterns,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),
            logical_geometry=[dict(label=n,shape=dict(x=0.,y=0.,r=100.,z=float(i+1))) for i,n in enumerate(labels)],
            enemy_healing=[dict(node='enemy-heal-'+str(i),targets=list(labels),amount=amount) for i in range(len(times))],
            contract=dict(scenario=label,skill_level=level,definitions=69,renewal=renew)))
    return rows
