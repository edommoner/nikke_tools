"""Inspect the exact input to a retained historical inverse, after newer inverses."""
from unittest.mock import patch


def stage_inputs(root, module, runner=None):
    observed = {}
    original = module.baseline_source
    def capture(root, name, source, **kwargs):
        observed[name] = (source, kwargs)
        return original(root, name, source, **kwargs)
    with patch.object(module, 'baseline_source', capture):
        (runner or module.project_sources)(root)
    return observed
