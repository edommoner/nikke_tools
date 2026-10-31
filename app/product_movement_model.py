"""Explicit product movement model using checked native consumers.

The numeric point/shape providers are the same common-policy functions used
by the coordinate reference suites. No position or actor history is an input.
"""
import copy
from contextlib import contextmanager


def normalize(value):
    from product_coordinate_model import normalize as coordinates
    from enemy_movement_model import normalize as motion
    if type(value) is not dict or set(value)!={'coord','logical_geometry','motion'}:
        raise ValueError('Movement requires explicit coord, logical_geometry and motion')
    result=coordinates(value['coord'],value['logical_geometry']);rules=motion(value['motion'])
    if [r['label'] for r in result['logical_geometry']]!=[r['label'] for r in rules['actors']]:
        raise ValueError('Movement collider and motion order must match exactly')
    return dict(result,motion=rules)


def public(data):
    result=copy.deepcopy(data)
    for frame in result['frames']:
        for segment in frame['segments']:segment.pop('fields',None)
    return result


@contextmanager
def execution(spec):
    import engine_worker  # Resolve before the movement adapter rewrites simulate.
    from enemy_movement_model import enemy_movement
    from product_coordinate_model import execution as coordinates
    with enemy_movement(spec['motion']) as movement,coordinates(spec):yield movement
