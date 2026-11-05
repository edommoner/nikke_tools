"""Real physical packet producer under the selected common landing policy.

This is a private reference, not historical CPU equivalence or GPU admission.
Only Geometry's landing provider changes. Damage, packet expansion, callbacks,
target retirement and scheduling remain the canonical battle implementation.
The process-global patch is scoped and must not be used concurrently.
"""
from contextlib import contextmanager
from unittest.mock import patch

REFERENCE_KIND = 'deterministic-common-cpu'
CONTRACT = 'coordinate-landing-v1'


def common_landing(ax, ay, radius, targets, core=None, grow=0., k=None):
    import engine_worker
    from calculator import aim
    from coordinate_landing_reference import landing

    def shape(value):
        return (1 if value.is_circle else 2, value.x, value.y, value.r,
                value.w, value.h, value.rot)

    result = landing(dict(aim=[ax, ay], radius=radius, grow=grow,
                          k=aim.MODEL_N if k is None else k,
                          targets=[shape(value) for value in targets],
                          core=None if core is None else shape(core)))
    return aim.Landing(front=tuple(result['front']),
                       reach=tuple(result['reach']),
                       core_open=result['core_open'],
                       core_under=result['core_under'])


@contextmanager
def common_policy():
    import engine_worker
    from calculator import boss_pattern, timeline
    original = timeline.simulate

    def expected_battle(*args, **kwargs):
        if kwargs.get('config', {}).get('rng_mode') != 'expected':
            raise ValueError('Common physical reference requires expected mode')
        return original(*args, **kwargs)

    with patch.object(boss_pattern, 'landing', common_landing), \
            patch.object(timeline, 'simulate', expected_battle):
        yield


def observe(case):
    import engine_worker
    from world_coordinate_physical_native import observe as native
    with common_policy():
        result = native(case)
    if any(row['expected'] is not True for row in result['physical_pellets']):
        raise ValueError('Common physical reference requires expected mode')
    result.update(reference_kind=REFERENCE_KIND, contract=CONTRACT,
                  scope='Common-policy CPU physical battle; no GPU admission')
    return result
