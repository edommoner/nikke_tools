"""Literal private shooting controls after unchanged canonical preparation."""
import copy
from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def configured(body,controls):
    import engine_worker
    if not isinstance(controls,dict) or any(name not in body['squad'] or not isinstance(value,dict) for name,value in controls.items()):raise ValueError('Expected literal member shooting controls')
    original=engine_worker.sim.prepare
    def prepare(request):
        run=original(request);run.squad=copy.deepcopy(run.squad)
        for char in run.squad:
            if char['name'] in controls:char['control']={**char.get('control',{}),**copy.deepcopy(controls[char['name']])}
        return run
    with patch.object(engine_worker.sim,'prepare',prepare):yield
