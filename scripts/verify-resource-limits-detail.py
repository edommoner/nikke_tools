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
from gpu_selector import Cuda
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


def quantities(device, backend):
    rows = []
    fixtures = [(name, initial, request, floor, after, int(spent), 'gauge_consume_as_ammo')
                for name, initial, request, floor, after, spent in CASES]
    fixtures.append(('plain-consume-has-no-ammo-events', 13, -1, 1, 1, 0, 'gauge_consume'))
    for name, initial, request, floor, after, ammo_events, stat in fixtures:
        effects = [(E('initial', 'instant', 'gauge_charge', initial, gauge_id='fuel'), N[0]),
                   (E('consume', 'instant', stat, request, event='on_attack', gauge_id='fuel', minimum_remaining=floor), N[0]),
                   (E('ammo events', 'buff', 'atk_pct', 1, event='squad_ammo_consume:1', max_stack=100), N[1])]
        if name in ('zero', 'below-minimum'):
            effects += [(E('charge events', 'buff', 'atk_dmg_pct', 1, event='every_stack:fuel:1', max_stack=100), N[0]),
                        (E('new resource condition', 'buff', 'crit_dmg', 9, event='passive', condition=['gauge_above:fuel:1']), N[0])]
        program = g.compile_effects(primitive.characters(N), effects)
        stats = {n: dict(atk=1000, hp=10000, **{'def': 100}) for n in N}
        result = g.run(device, [program], [[0, 0, 0, 0, 0, -1, 0, 0], [.1, 0, 7, 0, 0, -1, 0, 0],
            [.1, 2, 102, 0, program['states']['fuel'], 0, 0, 0], [.1, 2, 103, 1, 0, 1, 0, 0],
            [.1, 2, 103, 0, 10, 2, 0, 0], [.1, 2, 103, 0, 6, 3, 0, 0]], [[0, 0]], [stats], module_backend=backend)
        queries = result['queries'][0]
        actual, events = queries[0][0], queries[1][0]
        assert actual == after and events == ammo_events, (name, actual, events, after, ammo_events)
        if name in ('zero', 'below-minimum'):
            assert queries[2][0] == 0 and queries[3][0] == 9, (name, queries)
        rows.append(dict(name=name, passed=True, expected_remaining=after, remaining=actual,
                         expected_ammo_events=ammo_events, ammo_events=events,
                         charge_event_spy_enabled=name in ('zero', 'below-minimum'),
                         floor_did_not_emit_charge_events=queries[2][0] == 0 if name in ('zero', 'below-minimum') else None))
    return rows


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


def squad_cases(device, backend, cpu_only=False):
    rows = []
    original = BuffManager._dispatch_instant
    for name, owner, effects in scenarios():
        observed = []
        def dispatch(manager, effect, caster, t, *args, **kwargs):
            watched = caster == owner and 'minimum_remaining' in effect
            gid = effect.get('gauge_id', '')
            before = manager.state.get('gauges', {}).get(caster, {}).get(gid, 0)
            result = original(manager, effect, caster, t, *args, **kwargs)
            if watched:
                registration = bool(effect.get('tick_interval')) and not kwargs.get('from_tick', args[0] if args else False)
                witness = sum(ab.stack * ab.effect['fixed_value'] for ab in manager._active
                              if ab.caster == caster and ab.effect.get('name') == 'parent spend witness' and t < ab.expires_at)
                observed.append(dict(time=t, before=before, after=manager.state['gauges'][caster][gid], minimum=effect['minimum_remaining'], registration=registration, spend_witness=witness))
            return result
        body = body_for(N, 8, True);body.update(seed=12345, burst_gauge_mode='fixed')
        with v.custom_effects({owner: effects}), patch.object(BuffManager, '_dispatch_instant', dispatch):
            if cpu_only:
                result = a.evaluate(body);row = dict(name=name, passed=True, cpu_total=result['total_damage'])
            else:
                row = v.full.compare(device, name, body, module_backend=backend)
        assert observed and any(not o['registration'] for o in observed), (name, observed)
        assert all(o['after'] == o['before'] if o['registration'] else o['after'] >= o['minimum'] for o in observed), (name, observed)
        if name == 'nested-refill-does-not-change-parent-spend':
            assert all(o['spend_witness'] == 34 for o in observed), (name, observed)
        row['consumptions'] = observed;rows.append(row)
        print(json.dumps(dict(name=name, passed=row['passed'], consumptions=observed)), flush=True)
    return rows


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
    compiled=a.evaluate({**body, '_compile_gpu_detail': True})
    assert compiled['program']['counter_single_body']
    return dict(name='raw-consumption-data-correction-only', passed=True, consumptions=observed,
                single_body_program_compiles=True, capture_verification='scripts/verify-target-counters-detail.py')


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--backend', choices=('native', 'ptx'), default='native')
    parser.add_argument('--cpu-preflight', action='store_true');args = parser.parse_args()
    files = sorted({str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT / 'app').glob('*.py')}
        | {'app/detail_effects.cu', 'data/engine-effect-overrides.json', 'scripts/resource_limit_cases.py',
           'scripts/verify-resource-limits-detail.py', 'scripts/verify-gauge-detail.py', 'scripts/verify-extended-detail.py', 'scripts/verify-detail.py'})
    if not args.cpu_preflight:
        files += ['app/detail_effects-sm86.cubin', 'app/detail_effects-sm86.json'] if args.backend == 'native' else ['app/detail_effects.ptx', 'app/detail_effects-build.json']
    def hashes():return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
    before = hashes();device = None if args.cpu_preflight else Cuda()
    try:
        rows = ([] if args.cpu_preflight else quantities(device, args.backend)) + squad_cases(device, args.backend, args.cpu_preflight)
        if not args.cpu_preflight:rows += v.verify_primitives(device, args.backend)
        raw = raw_floor_control()
    finally:
        if device:device.close()
    assert before == hashes()
    report = dict(passed=all(r['passed'] for r in rows) and raw['passed'], cases=rows, raw_floor_control=raw,
        source_stable=True, source_sha256=before, cpu_trace_used_as_gpu_input=False,
        scope='Shared resource consumption only. New capture-model verification lives in verify-target-counters-detail.py; this report does not establish capture correctness.')
    suffix = 'cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT / f'research/resource-limits-{suffix}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':main()
