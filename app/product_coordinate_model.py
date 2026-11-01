"""Shared declared coordinate product context; no battle-state inputs."""
import sys
from pathlib import Path
import copy
from contextlib import contextmanager,nullcontext
from unittest.mock import patch


def normalize(coord,geometry,*,allow_empty=False):
    from calculator.boss_pattern import coord_spec
    from coordinate_logical_actor_geometry import normalize as shapes
    value=coord_spec(coord)
    if value is None or value.auto_aim is None:
        raise ValueError('Explicit common screen-space aim point required')
    return dict(coord=dict(auto_aim=list(value.auto_aim),pierce_px=value.pierce_px,explosion_scale=value.explosion_scale),logical_geometry=[] if allow_empty and type(geometry) is list and not geometry else shapes(geometry))


@contextmanager
def execution(spec,*,configure_run=False,typed_packets=False):
    # The shared geometry provider imports this adapter lazily. Resolve it
    # before checked simulation rewrites, including script-as-__main__ workers.
    import engine_worker
    from calculator import timeline,aim
    from coordinate_logical_actor_geometry import logical_actor_geometry
    from coordinate_typed_geometry_runtime import logical_typed_geometry
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
        with ((logical_typed_geometry if typed_packets else logical_actor_geometry)(spec['logical_geometry']) if spec['logical_geometry'] else nullcontext()),battle_attack_groups(routing='native',coordinate_packets=True,coordinate_typed_packets=typed_packets),patch.object(timeline,'sample_landing',sample),patch.object(aim.Shape,'dist',distance):
            if configure_run:
                from runner import sim
                original=sim.execute
                def execute(run,*args,**kwargs):
                    run.enemy['coord']=copy.deepcopy(spec['coord'])
                    run.expected=False;run.config['rng_mode']='random'
                    return original(run,*args,**kwargs)
                with patch.object(sim,'execute',execute):yield
            else:yield
    finally:timeline.random.setstate(state)


def normalize_product(value):
    if type(value) is not dict or set(value)!={'coord','logical_geometry'}:
        raise ValueError('Coordinate model requires explicit coord and logical_geometry')
    return normalize(value['coord'],value['logical_geometry'],allow_empty=True)


def public(spec):
    return dict(numeric_policy='common-software-binary64-v1',sampling_policy='seeded-mt19937-common-point-v1',logical_colliders=len(spec['logical_geometry']))
