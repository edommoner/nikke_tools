"""Resource minima, exact spend and event ordering; existing gauge oracle reused."""
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
from detail_coverage import a, body_for
from calculator.buff_manager import BuffManager
from resource_limit_cases import CASES
import detail_gpu as g


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


v = load('resource_gauge_oracle', 'scripts/verify-gauge-detail.py')
primitive = load('resource_primitive', 'scripts/verify-detail.py')
E, N = v.effect, v.NAMES




def scenarios():
    effects = [E('empty', 'instant', 'gauge_charge', 0, gauge_id='fuel'),
               E('periodic floor', 'instant', 'gauge_consume', 1, gauge_id='fuel', minimum_remaining=1,
                 tick_interval=.4, duration=7),
               E('floor condition', 'buff', 'atk_pct', 100, event='passive', condition=['gauge_above:fuel:1']),
               E('refill', 'instant', 'gauge_charge', 4, event='burst_cast', gauge_id='fuel')]
    yield 'periodic-minimum-and-live-passive', N[0], effects
    effects = [E('initial', 'instant', 'gauge_charge', 5, gauge_id='fuel'),
               E('consume window', 'buff', '', 0, event='burst_cast', duration=1),
               E('nested floor', 'instant', 'gauge_consume_as_ammo', 2, event='burst_cast', gauge_id='fuel', minimum_remaining=1),
               E('nested refill', 'instant', 'gauge_charge', 1, event='squad_ammo_consume:1', gauge_id='fuel',
                 condition=['self_state:consume window'], max_trigger=1),
               E('parent spend witness', 'buff', 'atk_dmg_pct', 17, event='squad_ammo_consume:1',
                 condition=['self_state:consume window'], duration=10, max_stack=100),
               E('close window', 'instant', 'remove_named_buff', 0, event='burst_cast', target_effect='consume window'),
               E('resource condition', 'buff', 'atk_pct', 100, event='passive', condition=['gauge_above:fuel:4']),
               E('entry floor', 'instant', 'gauge_consume_as_ammo', -1, event='full_burst_start', gauge_id='fuel', minimum_remaining=1)]
    yield 'nested-refill-does-not-change-parent-spend', N[2], effects




def raw_floor_control():
    owner = '일레그 : 붐 앤 쇼크'
    body = body_for([owner, '리타', '크라운', '앨리스', '모더니아'], 8, True)
    body.update(seed=12345, burst_gauge_mode='fixed')
    observed = [];original = BuffManager._dispatch_instant
    def dispatch(manager, effect, caster, t, *args, **kwargs):
        watched = caster == owner and 'minimum_remaining' in effect
        gid = effect.get('gauge_id', '')
        before = manager.state.get('gauges', {}).get(caster, {}).get(gid, 0)
        result = original(manager, effect, caster, t, *args, **kwargs)
        if watched:observed.append(dict(before=before, after=manager.state['gauges'][caster][gid], minimum=effect['minimum_remaining']))
        return result
    with patch.object(BuffManager, '_dispatch_instant', dispatch):a.evaluate(body)
    assert observed and all(o['after'] == max(1, o['before'] - 6) for o in observed), observed
    compiled=a.evaluate({**body, '_compile_detail': True})
    assert compiled['program']['counter_single_body']
    return dict(name='raw-consumption-data-correction-only', passed=True, consumptions=observed,
                single_body_program_compiles=True, capture_verification='scripts/verify-target-counters-detail.py')




if __name__ == '__main__':main()
