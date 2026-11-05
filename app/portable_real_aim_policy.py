"""Private literal environment policy after canonical full-profile preparation.

The public request adapter remains unchanged. Both native and static preparation
use the same explicit policy; no computed target, damage or shot is supplied.
"""
from contextlib import contextmanager
from unittest.mock import patch
import copy


@contextmanager
def configured(body,policy):
    import engine_worker
    if not isinstance(policy,dict) or set(policy)!={'aim_interrupt','camera','camera_mode'}:
        raise ValueError('Expected complete literal private aim policy')
    if type(policy['aim_interrupt']) is not bool or policy['camera_mode'] not in ('single','shared'):
        raise ValueError('Invalid private aim policy')
    cameras=policy['camera']
    if not isinstance(cameras,list) or len(cameras)!=len(set(cameras)) or any(n not in body['squad'] for n in cameras):
        raise ValueError('Private cameras must be unique members of the full roster')
    if policy['camera_mode']=='single' and len(cameras)>1:raise ValueError('Single camera policy requires at most one camera')
    original=engine_worker.sim.prepare
    def prepare(request):
        run=original(request);run.config=copy.deepcopy(run.config);run.config.update(copy.deepcopy(policy));return run
    with patch.object(engine_worker.sim,'prepare',prepare):yield
