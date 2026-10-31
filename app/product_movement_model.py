"""Explicit product movement model using checked native consumers.

The numeric point/shape providers are the same common-policy functions used
by the coordinate reference suites. No position or actor history is an input.
"""
import copy,sys
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch


def normalize(value):
    from calculator.boss_pattern import coord_spec
    from coordinate_logical_actor_geometry import normalize as geometry
    from enemy_movement_model import normalize as motion
    if type(value) is not dict or set(value)!={'coord','logical_geometry','motion'}:
        raise ValueError('Movement requires explicit coord, logical_geometry and motion')
    coord=coord_spec(value['coord'])
    if coord is None or coord.auto_aim is None:
        raise ValueError('Movement requires an explicit common screen-space aim point')
    shapes=geometry(value['logical_geometry']);rules=motion(value['motion'])
    if [r['label'] for r in shapes]!=[r['label'] for r in rules['actors']]:
        raise ValueError('Movement collider and motion order must match exactly')
    return dict(coord=dict(auto_aim=list(coord.auto_aim),pierce_px=coord.pierce_px,explosion_scale=coord.explosion_scale),
                logical_geometry=shapes,motion=rules)


def public(data):
    result=copy.deepcopy(data)
    for frame in result['frames']:
        for segment in frame['segments']:segment.pop('fields',None)
    return result


@contextmanager
def execution(spec):
    # The shared geometry provider imports this adapter lazily. Resolve it
    # before checked simulation rewrites, including script-as-__main__ workers.
    import engine_worker
    from calculator import timeline,aim
    from enemy_movement_model import enemy_movement
    from coordinate_logical_actor_geometry import logical_actor_geometry
    from battle_attack_group_runtime import battle_attack_groups
    from portable_coordinate_sample_v1 import sample
    # Reuse the independent common coordinate provider shipped with the proof
    # code; normal app workers do not otherwise add research to their path.
    with patch.object(sys,'path',[str(Path(__file__).resolve().parents[1]/'research'),*sys.path]):
        from coordinate_geometry_reference import evaluate
    # CPU and GPU use the existing deterministic common point/shape arithmetic.
    # The request Run explicitly selects random mode; do not rewrite simulation.
    def distance(shape,px,py):
        return evaluate((1 if shape.is_circle else 2,shape.x,shape.y,shape.r,shape.w,shape.h,shape.rot,px,py,0.,0.))['distance']
    state=timeline.random.getstate()
    try:
        with enemy_movement(spec['motion']) as movement,logical_actor_geometry(spec['logical_geometry']),battle_attack_groups(routing='native',coordinate_packets=True),patch.object(timeline,'sample_landing',sample),patch.object(aim.Shape,'dist',distance):
            yield movement
    finally:timeline.random.setstate(state)
