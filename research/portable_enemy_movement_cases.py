"""Original Yuni/Yan effects with explicit moving ADD collider declarations."""
import copy
from portable_original_identity_inventory import selected_profile_bodies


def fixtures():
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    sources={name:body for name,stage,body in selected_profile_bodies(['유니','얀'],0)}
    rows=[]
    for owner,scenario,count,renew in [('유니','disable',2,False),('얀','force',2,False),('유니','renewal',2,True),('유니','overlap-disable',2,False),('유니','overlap-force',2,False)]:
        body=copy.deepcopy(sources[owner]);body.update(duration=30,seed=4711)
        if scenario.startswith('overlap'):
            body['squad']=['얀' if name=='미란다' else name for name in body['squad']]
            body['profile']['chars'].pop('미란다')
            body['profile']['chars']['얀']=copy.deepcopy(sources['얀']['profile']['chars']['얀'])
        wave=dict(id='motion-wave',kind='summon',spec=dict(count=count,hp=1e30))
        if renew:wave.update(after=['start','motion-wave'],until=dict(time=12),repeat=3)
        patterns=[wave];body['enemy'].update(has_parts=False,patterns=copy.deepcopy(patterns))
        labels=[b.label for b in bindings(validate(patterns,coord=True)) if int(b.kind)==5]
        geometry=[dict(label=label,shape=dict(x=-200.,y=0.,r=30.,z=float(i+1))) for i,label in enumerate(labels)]
        movement=dict(precedence='disable-before-force',force_policy='snap-to-declared-center',recipient_policy='canonical-all-in-range',
            actors=[dict(label=label,velocity=[20.,0.],force_center=[0.,0.]) for label in labels])
        if scenario=='overlap-force':movement['precedence']='force-before-disable'
        rows.append(dict(name='enemy-movement/'+owner+'/'+scenario,body=body,patterns=patterns,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),logical_geometry=geometry,enemy_movement=movement,
            contract=dict(owner=owner,scenario=scenario)))
    return rows
