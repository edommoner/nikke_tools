"""Original rosters and sampled weapons under an explicit typed geometry policy."""
import copy,importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('coordinate_typed_weapon_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'))
    factory=importlib.util.module_from_spec(s);s.loader.exec_module(factory)
    rows=[]
    # Keep every original definition and weapon. Three seconds exercises real
    # charge/RL packets; one second isolates the frozen shotgun generation.
    for label,character,kind,capacity,shapes in (
        ('projectile-front','사쿠라',2,1e30,[dict(x=0.,y=0.,r=10000.,z=2.)]),
        ('projectile-miss','사쿠라',2,1e30,[dict(x=100000.,y=100000.,r=1.,z=2.)]),
        ('shotgun-frozen-generation','마르차나',2,1.,[dict(x=0.,y=0.,r=10000.,z=2.),dict(x=0.,y=0.,r=10000.,z=1.)]),
        ('shield-front','레이',3,1e30,[dict(x=0.,y=0.,r=10000.,z=2.)]),
        ('projectile-mixed-reach','사쿠라',2,1e30,[dict(x=0.,y=0.,r=10.,z=2.)]),
        ('canonical-front','사쿠라',2,1e30,[dict(x=0.,y=0.,r=10000.,z=2.)]),
        ('shield-stream-overflow','레이',3,1e30,[dict(x=0.,y=0.,r=10000.,z=2.)]),
    ):
        duration=30 if label=='shield-stream-overflow' else 1 if label=='shotgun-frozen-generation' else 3
        body=dict(factory.body_for(factory.policy.roster_for(character),duration),burst_gauge_mode='accumulate',seed=4301)
        patterns=[dict(id='typed-weapon-world',kind='idle',until=dict(time=duration))]
        if label=='canonical-front':patterns.append(dict(id='front-part',kind='parts',targets=[dict(name='front-part',hp=1e30,x=0.,y=0.,r=10000.,z=3.)]))
        # Scalar validation deliberately receives no coordinate shapes.
        body['enemy']['patterns']=copy.deepcopy(patterns[:1])
        rows.append(dict(name='coordinate-typed-weapon/'+label,character=character,body=body,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,
            coordinate_weapon_targets=True,max_attacks=128,
            typed_bindings=[dict(node=patterns[0]['id'],kind=kind,identity=10+i,capacity=capacity,**(dict(owner=[0,0,1]) if kind==3 else {})) for i in range(len(shapes))],
            typed_geometry=dict(point_source='caster_aim',shapes=shapes)))
    return rows

def prepare(row):
    from portable_coordinate_original_cases import prepare_case
    case,world=prepare_case(row)
    case.update({key:copy.deepcopy(row[key]) for key in ('body','coordinate_weapon_targets','typed_bindings','typed_geometry','max_attacks','character')})
    return case,world
