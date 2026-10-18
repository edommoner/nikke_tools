"""Shared cast/landing witnesses; reuse existing squad and legacy comparators."""
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
import detail_gpu as g


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


p = load('deferred_periodic', 'scripts/verify-periodic-detail.py')
legacy = load('deferred_legacy', 'scripts/verify-named-target-detail.py')
primitive = load('deferred_primitive', 'scripts/verify-detail.py')
E = p.effect


def quantities(device, backend):
    rows = []
    owner = p.NAMES[2]
    stats = {name: dict(atk=1000, hp=10000, **{'def': 100}) for name in p.NAMES}
    common = [E('no critical', 'buff', 'crit_rate', -15),
              E('drain', 'instant', 'current_hp_reduce', 50),
              E('lifesteal', 'buff', 'lifesteal_pct', 50),
              E('earlier ATK', 'buff', 'atk_pct', 10, event='burst_cast', duration=10)]
    later = [E('later excluded ATK', 'buff', 'atk_pct', 200, event='burst_cast', duration=10),
             E('entry ATK', 'buff', 'atk_pct', 100, event='full_burst_start', duration=10)]
    # Explicit independent quantities: name, hits, HP basis, modifier, side, damage.
    configs = [('baseline', 0, None, None, None, 0),
               ('one-hit', 1, None, None, None, 3000),
               ('three-hits', 3, None, None, None, 9000),
               ('magnitude-before', 1, None, 'magnitude', 'before', 6000),
               ('magnitude-after', 1, None, 'magnitude', 'after', 3000),
               ('HP-add-before', 1, 'max_hp_additive', 'HP', 'before', 6000),
               ('HP-add-after', 1, 'max_hp_additive', 'HP', 'after', 4500),
               ('HP-replace-before', 1, 'max_hp_replacement', 'HP', 'before', 2850),
               ('HP-replace-after', 1, 'max_hp_replacement', 'HP', 'after', 1350)]
    programs = []
    for name, count, basis, modifier, side, expected in configs:
        effects = copy.deepcopy(common)
        changed = (E('magnitude modifier', 'buff', 'dmg_scale_mag_pct', 100, event='burst_cast', duration=10, target_effect='landing') if modifier == 'magnitude' else
                   E('HP modifier', 'buff', 'max_hp_only_pct', 100, event='burst_cast', duration=10) if modifier == 'HP' else None)
        if side == 'before':effects.append(changed)
        attack_index = len(effects)
        if count:
            attack = E('landing', 'damage', 'sequential_damage:' + str(count), 100,
                       'target', event='burst_cast', land_in_full_burst=True)
            if basis:attack.update(scaling=basis, scaling_hp_pct=10)
            effects.append(attack)
        if side == 'after':effects.append(changed)
        effects += copy.deepcopy(later)
        chars = primitive.characters(p.NAMES)
        for char in chars:
            char['_weapon'] = copy.deepcopy(char['_weapon'])
            char['_weapon']['damage_coeff'] = 0
            char['_detail_stage'] = int(char['_weapon']['burst_stage'])
            char['_detail_innate_stage'] = char['_detail_stage']
        program = g.compile_effects(chars, [(e, owner) for e in effects])
        if count:
            # Explicit instruction fixture; compile_full's mask is independently
            # exercised by the grown-squad cases with nested callbacks.
            for index, effect in enumerate(effects[attack_index + 1:], attack_index + 1):
                if effect['type'] == 'buff' and 'burst_cast' in effect['trigger']['timing']:
                    row = program['effects'][attack_index]
                    word = g.B3_MASK + index // 32
                    row[word] = int(row[word]) | 1 << (index % 32)
        programs.append(program)
    script = [[0, 0, 0, who, 0, -1, 0, 0] for who in range(5)]
    for frame in range(241):
        script.append([frame / 60, 4, 0, 0, 0, -1, 0, 0])
        if frame in (214, 215):
            script.append([frame / 60, 2, 101, 2, 0, frame - 214, 0, 0])
    result = g.run(device, programs, script, [[100, 0]] * len(programs), [stats] * len(programs), module_backend=backend)
    baseline_damage = result['totals'][0][2]
    baseline_hp = result['queries'][0][1][0]
    # Ordinary: (1000*(1 + (10+100)/100) - 100) *1.5 =3000.
    # HP addition contributes1000 or2000 before defense; replacement discards
    # the original ATK and uses1000 or2000. Magnitude-before doubles coefficient.
    for index, (name, count, basis, modifier, side, expected) in enumerate(configs[1:], 1):
        damage = result['totals'][index][2] - baseline_damage
        before_healing = result['queries'][index][0][0] - result['queries'][0][0][0]
        healing = result['queries'][index][1][0] - baseline_hp
        assert damage == expected, (name, damage, expected)
        assert before_healing == 0, (name, before_healing)
        assert healing == expected / 2, (name, healing, expected / 2)
        rows.append(dict(name='independent-' + name, passed=True,
                         expected_damage=expected, damage=damage,
                         expected_healing=expected / 2, healing=healing,
                         healing_before_landing=before_healing, same_frame_witness=215 / 60))
    return rows


def scenarios():
    for name, stat, enabled, owner, expected in (
        ('literal-parent-and-children', 'sequential_damage:3', True, 2, 3),
        ('latched-reference-and-gate', 'sequential_damage:cast count', True, 2, 1),
        ('zero-count', 'sequential_damage:0', True, 2, 0),
        ('negative-count', 'sequential_damage:-2', True, 2, 0),
        ('missing-reference', 'sequential_damage:absent', True, 2, 0),
        ('disabled-landing', 'sequential_damage:3', False, 2, 3),
        ('stage-two-is-immediate', 'sequential_damage:3', True, 1, 3),
        ('legacy-and-delayed-coexist', 'sequential_damage:3', True, 2, 3),
        ('query-scope-additive', 'sequential_damage:3', True, 2, 3),
        ('query-scope-replacement', 'sequential_damage:3', True, 2, 3),
    ):
        count = E('cast count', 'buff', '', 0, max_stack=9)
        count['trigger']['timing'] = ['battle_start', 'full_burst_start']
        effects = [count, E('cast gate', 'buff', '', 0),
                   E('earlier ATK', 'buff', 'atk_pct', 10, event='burst_cast', duration=10),
                   E('landing', 'damage', stat, 100, 'target', event='burst_cast',
                     land_in_full_burst=enabled, condition=['self_state:cast gate'], max_trigger=1),
                   E('consume gate', 'instant', 'remove_named_buff', 0, event='burst_cast', target_effect='cast gate'),
                   E('later ATK', 'buff', 'atk_pct', 200, event='burst_cast', duration=10),
                   E('entry ATK', 'buff', 'atk_pct', 100, event='full_burst_start', duration=10),
                   E('child attack', 'damage', 'damage', 100, 'target', event='hit_count:landing:1'),
                   E('child changes ATK', 'buff', 'atk_pct', 20, event='hit_count:landing:1', max_stack=20)]
        if name == 'legacy-and-delayed-coexist':
            effects.insert(4, E('legacy bonus', 'damage', 'bonus_damage', 50, 'target', event='burst_cast'))
        if name.startswith('query-scope-'):
            attack = next(e for e in effects if e['name'] == 'landing')
            attack.update(scaling='max_hp_additive' if name.endswith('additive') else 'max_hp_replacement', scaling_hp_pct=10)
            index = effects.index(attack)
            effects[index:index] = [E('earlier HP', 'buff', 'max_hp_only_pct', 50, event='burst_cast', duration=10),
                                    E('earlier magnitude', 'buff', 'dmg_scale_mag_pct', 50, event='burst_cast', duration=10, target_effect='landing')]
            effects[index + 3:index + 3] = [E('later HP', 'buff', 'max_hp_only_pct', 100, event='burst_cast', duration=10),
                                           E('later magnitude', 'buff', 'dmg_scale_mag_pct', 100, event='burst_cast', duration=10, target_effect='landing'),
                                           E('child magnitude', 'buff', 'dmg_scale_mag_pct', 100, event='burst_cast', duration=10, target_effect='child attack')]
        yield name, owner, effects, expected, enabled and owner == 2


def verify(device, backend, cpu_only=False):
    rows = []
    original_notify = BuffManager.notify
    original_activate = BuffManager._activate
    for name, slot, effects, expected_hits, delayed in scenarios():
        owner = p.NAMES[slot]
        observed = dict(casts=[], hits=[])

        def activated(manager, effect, caster, t, *args, **kwargs):
            if caster == owner and effect.get('name') == 'landing':
                observed['casts'].append(t)
            return original_activate(manager, effect, caster, t, *args, **kwargs)

        def notified(manager, event, t, caster, **ctx):
            if caster == owner and event == 'hit_count:landing':
                observed['hits'].append(dict(time=t, full=bool(manager.state.get('full_burst')),
                                             live_count=manager.ref_count(caster, 'cast count')))
            return original_notify(manager, event, t, caster, **ctx)

        body = body_for(p.NAMES, 8, True)
        body.update(seed=12345, shooting_policy='character', burst_gauge_mode='fixed')
        with p.custom_effects({owner: effects}), patch.object(BuffManager, '_activate', activated), patch.object(BuffManager, 'notify', notified):
            if cpu_only:
                result = a.evaluate(body)
                row = dict(name=name, passed=True, cpu_total=result['total_damage'])
            else:
                row = p.full.compare(device, name, body, module_backend=backend)
        assert observed['casts'], (name, observed)
        assert len(observed['hits']) == expected_hits, (name, observed, expected_hits)
        assert all(hit['full'] == delayed for hit in observed['hits']), (name, observed, delayed)
        if name == 'latched-reference-and-gate':
            assert observed['hits'][0]['live_count'] == 2, observed
        row.update(observed=observed, expected_hits=expected_hits, landing_after_full_burst=delayed)
        rows.append(row)
        print(json.dumps(dict(name=name, passed=row['passed'], observed=observed)), flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=('native', 'ptx'), default='native')
    parser.add_argument('--cpu-preflight', action='store_true')
    args = parser.parse_args()
    files = sorted({str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT / 'app').glob('*.py')}
                   | {'app/detail_effects.cu', 'scripts/verify-deferred-attack-detail.py',
                      'scripts/verify-periodic-detail.py', 'scripts/verify-extended-detail.py',
                      'scripts/verify-detail.py', 'scripts/verify-named-target-detail.py'})
    if not args.cpu_preflight:
        files += ['app/detail_effects-sm86.cubin', 'app/detail_effects-sm86.json'] if args.backend == 'native' else ['app/detail_effects.ptx', 'app/detail_effects-build.json']
    def hashes():
        return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
    before = hashes()
    device = None if args.cpu_preflight else Cuda()
    try:
        rows = ([] if args.cpu_preflight else quantities(device, args.backend)) + verify(device, args.backend, args.cpu_preflight)
        if not args.cpu_preflight:
            rows += legacy.phase_cases(device, args.backend)
    finally:
        if device:
            device.close()
    assert before == hashes()
    report = dict(passed=all(row['passed'] for row in rows), cases=rows,
                  source_stable=True, source_sha256=before, cpu_trace_used_as_gpu_input=False,
                  scope='Shared cast/landing scheduling and legacy B3 bonus interaction; no new real character acceptance claim')
    suffix = 'cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT / f'research/deferred-attack-{suffix}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
