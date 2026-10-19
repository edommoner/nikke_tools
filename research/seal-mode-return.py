"""Seal the fixed mode-return source only after shared/real/API/remote gates."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

R = Path(__file__).resolve().parents[1]
P = R / 'research'
SOURCE = 'a7f478452f7d9c3dbdca97879a2efdf8634c38a9'
sys.path[:0] = [str(R / d) for d in ('app', 'scripts')]


def load(name):
    return json.loads((P / (name + '.json')).read_text())


def save(name, value):
    (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(raw):
    text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    text = '\n'.join(line for line in text.split('\n') if not re.match(r'^\s*#line\b', line))
    return re.sub(r'"([^"\n]+)"', lambda m: '"' + m[1].replace('\\', '/').split('/')[-1] + '"' if '/' in m[1] or '\\' in m[1] or m[1] == 'slang-cuda-prelude.h' else m[0], text).encode('utf-8')


def main():
    m = load('portable-combat-metal')
    w = load('windows-portable-combat-v47')
    gates = load('portable-mode-return-global-gates')
    transfer = load('portable-mode-return-transfer-completed')
    assert m['passed'] and m['gpu_execution_verified'] and len(m['cases']) == 1139 and len(m['rejected_cases']) == 206
    assert len(m['mode_session_cpu_regressions']) == 29
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 18
    assert transfer['passed'] and transfer['remote_turn_status'] == 'completed' and transfer['parts'] == 22
    assert w['passed'] and w['gpu_execution_verified'] and w['execution']['commit'] == SOURCE
    assert w['execution']['exit_code'] == 0 and not w['execution']['timed_out']
    assert w['execution']['below_normal_priority'] and w['execution']['timeout_seconds'] == 120
    assert w['postcheck']['remaining_verification_processes'] == 0
    for key in ('head', 'status'):
        assert w['postcheck']['original_' + key + '_after'] == w['execution']['original_' + key + '_before']
    keys = ['source_sha256', 'input_sha256', 'output_sha256', 'validation_sha256', 'actual_statuses',
            'expected_statuses', 'batch_layout', 'rejected_cases', 'known_cpu_differences',
            'known_health_cpu_differences', 'known_mode_cpu_differences']
    keys += sorted(k for k in m if k.endswith('_cpu_regressions'))
    for key in keys:
        assert w[key] == m[key], key
    assert w['cases'] == [dict(name=c['name'], passed=c['passed']) for c in m['cases']]
    for key in ('source_sha256', 'validation_sha256'):
        for path, digest in m[key].items():
            assert sha(R / path) == digest, path
    normalized = {}
    for backend, suffix in [('cuda', 'cu'), ('metal', 'metal')]:
        path = P / 'portable-build' / ('event_runtime.' + suffix)
        assert sha(path) == m['generated_sha256'][backend]
        normalized[backend] = hashlib.sha256(normalize(path.read_bytes())).hexdigest()
        assert normalized[backend] == w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256'], backend
    save('portable-generated-v47-comparison', dict(passed=True, source_commit=SOURCE, compared_keys=keys,
                                                  normalized_sha256=normalized, maximum_frame_depth_also_exactly_equal=True))
    roster = load('portable-roster-battles-metal')
    assert roster['passed'] and len(roster['cases']) == 58
    assert all(c['passed'] and not c['differences'] for c in roster['cases'])
    old_roster = json.loads(subprocess.check_output(['git', 'show', '76e0c08:research/portable-roster-battles-metal.json'], cwd=R))
    strip_wall = lambda c: {k: v for k, v in c.items() if k != 'cpu_reference_wall_seconds'}
    assert [strip_wall(c) for c in roster['cases']] == [strip_wall(c) for c in old_roster['cases']]
    for name in ('portable-api-metal', 'portable-catalog-weapons-metal', 'portable-real-equipment-metal',
                 'portable-real-battle-metal', 'portable-events-metal', 'portable-metal-pipeline-lock',
                 'portable-numeric-metal', 'portable-probe-metal'):
        assert load(name)['passed'], name
    spec = importlib.util.spec_from_file_location('mode_cases', R / 'scripts/verify-portable-combat.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    from portable_burst_oracle import observe
    rows = []
    resolved = {'mode-duration-restores-base', 'mode-round-limit-restores-magazine',
                'reload-callback-selects-new-mode-before-fire', 'charge-mode-entry-and-round-exit',
                'finite-timed-mode-stalls-on-empty'}
    for case, gpu in zip(verifier.fixtures(), m['results']):
        if case['name'] in resolved or case['name'].startswith('continuous-return-'):
            native = observe(case)
            assert len(gpu['queries']) == len(native['queries'])
            verifier.contains(gpu['queries'], native['queries'], case['name'])
            rows.append(dict(name=case['name'], passed=True, native=native))
    assert len(rows) == 13
    save('portable-mode-return-native', dict(passed=True, cases=rows, source_commit=SOURCE,
                                            cpu_trace_used_as_gpu_input=False,
                                            unresolved_raw_cpu_mode_cases=['mode-toggle-end-child-reentry', 'mode-replacement-first-shot-coefficient'],
                                            existing_declared_difference='mode-expiry-end-child-starts-fresh-session'))
    units = next(g for g in gates['gates'] if g['name'] == 'unit')
    text = Path(units['log']).read_text()
    assert units['exit_code'] == 0 and re.search(r'Ran 128 tests\b', text) and text.rstrip().endswith('OK')
    save('portable-mode-return-unit-tests', dict(passed=True, tests=128, output=text))
    for name, count in [('staged-native', 9), ('source-native', 6)]:
        gate = next(g for g in gates['gates'] if g['name'] == name)
        assert gate['exit_code'] == 0 and f'Ran {count} tests' in Path(gate['log']).read_text()
    save('portable-mode-return-native-runtime-tests', dict(passed=True, tests=15,
         outputs={name: Path(next(g for g in gates['gates'] if g['name'] == name)['log']).read_text()
                  for name in ('staged-native', 'source-native')}))
    prototype = load('portable-mode-return-parity')
    benchmark = load('portable-mode-return-benchmark')
    assert prototype['passed'] and prototype['inputs'] == 1139 and prototype['all_output_words_equal']
    assert prototype['variants']['separate']['output_sha256'] == prototype['variants']['nested']['output_sha256']
    assert benchmark['passed'] and benchmark['production_change_adopted'] is False
    assert prototype['production_source_sha256'] == benchmark['production_source_sha256'] == m['source_sha256']
    measurements = {}
    for name, workload in benchmark['workloads'].items():
        values = {v: [r['transport']['gpu_seconds'] for r in rows[1:]] for v, rows in workload['samples'].items()}
        assert all(len(rows) == 4 and rows[0]['warmup'] and all(not row['warmup'] for row in rows[1:]) for rows in workload['samples'].values())
        assert len({r['output_sha256'] for rows in workload['samples'].values() for r in rows}) == 1
        ranges = {v: [min(rows), max(rows)] for v, rows in values.items()}
        overlap = max(ranges['separate'][0], ranges['nested'][0]) <= min(ranges['separate'][1], ranges['nested'][1])
        measurements[name] = dict(median_gpu_seconds=workload['median_gpu_seconds'], ratio=workload['nested_to_separate_ratio'], ranges=ranges, ranges_overlap=overlap)
    assert all(row['ranges_overlap'] for row in measurements.values())
    parity = load('portable-mode-return-existing-parity')
    assert parity['previous_cases'] == 1131 and parity['unchanged_full_states'] == 1125
    assert len(parity['changed_cases']) == 6 and len(parity['added_cases']) == 8
    assert parity['unchanged_real_profiles'] == 58 and not parity['real_profile_differences']
    save('portable-combat-cuda', dict(w, summary_only=True, summary_source='windows-portable-combat-v47.json', scope=m['scope']))
    previous = json.loads(subprocess.check_output(['git', 'show', '3ff4eda:research/portable-combat-checkpoint.json'], cwd=R))
    save('portable-combat-v46-checkpoint', previous)
    checkpoint = copy.deepcopy(previous)
    checkpoint.update(verified_commit=SOURCE, source_provenance=dict(fixed_shared_source_commit=SOURCE,
                      metal_core_report_source_commit=SOURCE, windows_source_commit=SOURCE),
                      previous_checkpoint=dict(report='portable-combat-v46-checkpoint.json', proof_commit='3ff4eda'),
                      positive_cases=1139, rejections=206, batched_inputs=1345, unit_tests=128,
                      windows_report='windows-portable-combat-v47.json', windows_checks_this_stage=1,
                      windows_execution=w['execution'], windows_postcheck=w['postcheck'],
                      regressions={k: v for k, v in m.items() if k.endswith('_cpu_regressions')},
                      generated_source_comparison='portable-generated-v47-comparison.json',
                      validation_receipt='portable-mode-return-validation.json',
                      existing_parity='portable-mode-return-existing-parity.json',
                      mode_return_pending_uses_existing_state=True, mode_return_added_private_arrays=0,
                      unresolved_raw_cpu_mode_cases=['mode-toggle-end-child-reentry', 'mode-replacement-first-shot-coefficient'],
                      mode_return_efficiency_evaluated=True,
                      mode_return_efficiency_production_change_adopted=False,
                      mode_return_efficiency_measurements=measurements,
                      mode_return_efficiency_decision='Retain verified separate guard: the two equivalent variants have overlapping sample ranges in both limited workloads; first workload is especially variable.',
                      next_work=['Resolve same-frame replacement/reentry CPU session carryover against the common fresh-session contract',
                                 'Connect remaining lifecycle, world and effect families for all 203 characters; full certification remains 0/203'])
    for key in ('source_sha256', 'input_sha256', 'output_sha256', 'validation_sha256'):
        checkpoint[key] = m[key]
    checkpoint['cuda_comparison'] = {key: True for key in keys}
    checkpoint.pop('windows_baseline_execution', None)
    checkpoint.pop('prototype_source_commit', None)
    save('portable-combat-checkpoint', checkpoint)
    reports = ['portable-combat-metal', 'portable-combat-cuda', 'windows-portable-combat-v47',
               'portable-mode-return-native', 'portable-mode-return-unit-tests', 'portable-mode-return-global-gates',
               'portable-mode-return-transfer-completed', 'portable-generated-v47-comparison',
               'portable-mode-return-existing-parity', 'portable-roster-battles-metal',
               'portable-api-metal', 'portable-catalog-weapons-metal', 'portable-real-equipment-metal',
               'portable-real-battle-metal', 'portable-combat-checkpoint', 'portable-mode-return-native-runtime-tests',
               'portable-mode-return-parity', 'portable-mode-return-benchmark', 'portable-mode-return-timing-order',
               'portable-mode-return-benchmark-script-failure', 'portable-events-metal', 'portable-numeric-metal',
               'portable-probe-metal', 'portable-metal-pipeline-lock', 'portable-duration-extend-metal',
               'portable-definition-input-metal', 'portable-definition-scalar-metal', 'portable-definition-out-metal',
               'portable-removal-queue-metal', 'portable-catalog-readiness']
    save('portable-mode-return-validation', dict(passed=True, source_commit=SOURCE, positives=1139, rejections=206,
         native_mode_cases=29, added_continuous_cases=8, unit_tests=128, native_runtime_tests=15, real_profiles=58,
         windows_runs=1, unresolved_raw_cpu_mode_cases=checkpoint['unresolved_raw_cpu_mode_cases'],
         efficiency_evaluated=True, efficiency_production_change_adopted=False,
         full_goal_complete=False, full_character_verified=0,
         artifact_sha256={str((P / (name + '.json')).relative_to(R)): sha(P / (name + '.json')) for name in reports},
         tool_sha256={str(path.relative_to(R)): sha(path) for path in [P / 'benchmark-mode-return.py', P / 'run-mode-return-gates.py', P / 'seal-mode-return.py']}))
    print('Mode return sealed: 1139/206, native 29, units 128, 58 real profiles; full goal remains incomplete')


if __name__ == '__main__':
    main()
