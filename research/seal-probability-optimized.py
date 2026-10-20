"""Seal adopted scalar accessors only after both GPUs and all Mac gates finish."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'research'
SOURCE = '2b89babe0bd6ffa16c9b8b315de3137e7da669c8'
BASELINE = '988858f853594e2a0770640fa21bbd94d7c08cc0'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())


def save(name, value):
    (REPORTS / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(args):
    gates = load('portable-probability-optimized-global-gates')
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 32
    assert gates['source_commit'] == SOURCE
    assert all(row['exit_code'] == 0 and row['source_commit'] == SOURCE for row in gates['gates'])
    processes = []
    markers = [' research/run-', ' research/verify-', ' scripts/verify-portable-',
               '/scripts/run-metal-probe.swift', ' research/benchmark-', ' research/capture-']
    for line in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,etime=,command='], text=True).splitlines():
        parts = line.split(None, 3)
        if len(parts) != 4:
            continue
        pid, ppid, elapsed, command = parts
        if int(pid) == os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh', '/bin/bash')):
            continue
        if any(marker in command for marker in markers):
            processes.append(dict(pid=int(pid), ppid=int(ppid), elapsed=elapsed, command=command))
    assert not processes, processes
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=ROOT, check=True)
    windows_path = 'research/windows-portable-probability-v68.json'
    receipt_path = 'research/portable-probability-optimized-cuda-readback.json'
    changed_paths = subprocess.check_output([
        'git', 'diff-tree', '--no-commit-id', '--name-only', '-r', args.artifact_commit
    ], cwd=ROOT, text=True).splitlines()
    assert changed_paths == sorted([windows_path, receipt_path])
    parent = subprocess.check_output(['git', 'rev-parse', args.artifact_commit + '^'], cwd=ROOT, text=True).strip()
    assert parent == SOURCE
    for path, expected in [(windows_path, args.windows_sha256), (receipt_path, args.readback_sha256)]:
        data = (ROOT / path).read_bytes()
        assert sha(data) == expected and git_bytes(args.artifact_commit, path) == data, path
    m = load('portable-combat-metal')
    w = load('windows-portable-probability-v68')
    assert m['passed'] and w['passed'] and m['gpu_execution_verified'] and w['gpu_execution_verified']
    assert m['backend'] == 'metal' and w['backend'] == 'cuda'
    assert len(m['cases']) == 1940 and len(m['rejected_cases']) == 340
    assert len(m['element_override_cpu_regressions']) == 156
    keys = ['source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256',
            'actual_statuses', 'expected_statuses', 'batch_layout', 'rejected_cases', 'cases']
    keys += [key for key in m if key.endswith('_cpu_regressions') or key.startswith('known_')]
    for key in keys:
        assert m[key] == w[key], key
    for path in ['research/verify-probability-optimized.py', 'research/verify-probability-regression.py',
                 'research/run-probability-optimized-gates.py']:
        assert (ROOT / path).read_bytes() == git_bytes(SOURCE, path), path
    parity = m['probability_existing_parity']
    assert parity['passed'] and parity['all_old_output_words_equal'] and parity['no_output_normalization']
    assert parity['prior_inputs'] == 2182 and parity['current_inputs'] == 2280
    assert parity['driver_sha256'] == sha((REPORTS / 'verify-probability-regression.py').read_bytes())
    for key in parity:
        if key not in ['evidence', 'input_path', 'raw_path']:
            assert parity[key] == w['probability_existing_parity'][key], key
    baseline = json.loads(git_bytes(BASELINE, 'research/portable-combat-metal.json'))
    readbacks = {}
    for backend in ['metal', 'cuda']:
        receipt = load('portable-probability-optimized-' + backend + '-readback')
        assert receipt['passed'] and receipt['source_commit'] == SOURCE
        assert receipt['input_equal'] and receipt['output_equal'] and receipt['programs'] == 2280
        assert receipt['baseline_proof_commit'] == BASELINE and not receipt['gpu_execution_reused']
        assert receipt['no_gpu_retry'] and receipt['no_output_normalization']
        for key in ['input_sha256', 'output_sha256']:
            assert receipt[key] == receipt['evidence'][key] == baseline[key] == m[key]
        assert receipt['driver_sha256'] == sha(git_bytes(SOURCE, 'research/verify-probability-optimized.py'))
        assert len(receipt['actual_block_sha256']) == 2280
        readbacks[backend] = receipt['actual_block_sha256']
    assert readbacks['metal'] == readbacks['cuda']
    candidate = load('portable-probability-candidate-parity')
    candidate_key = 'research/portable-build/probability-accessors/gpu/event_runtime.slang'
    assert sha((ROOT / 'gpu/event_runtime.slang').read_bytes()) == candidate['parity']['accessors']['source_sha256'][candidate_key]
    spec = importlib.util.spec_from_file_location('normalizer', REPORTS / 'seal-stack-increment.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    normalized = {}
    for backend, suffix in [('cuda', 'cu'), ('metal', 'metal')]:
        path = REPORTS / 'portable-build' / ('event_runtime.' + suffix)
        assert sha(path.read_bytes()) == m['generated_sha256'][backend]
        normalized[backend] = helper.normalized(path.read_bytes())
        assert normalized[backend] == w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
    execution, post = w['execution'], w['postcheck']
    assert execution['commit'] == SOURCE and execution['exit_code'] == 0 and not execution['timed_out']
    assert execution['below_normal_priority'] and execution['timeout_seconds'] == 120
    assert post['residual_verification_process_count'] == 0 and not post['residual_verification_processes']
    assert post['existing_gpu_service_preserved']
    for field in ['head', 'status']:
        assert execution['original_' + field + '_before'] == post['original_' + field + '_after']
    old_roster = json.loads(git_bytes(BASELINE, 'research/portable-roster-battles-metal.json'))
    roster = load('portable-roster-battles-metal')
    assert roster['passed'] and len(roster['cases']) == 102
    assert len(old_roster['cases']) == 102
    lookup = {(c['character'], c['grown']): c for c in roster['cases']}
    for case in old_roster['cases']:
        now = lookup[case['character'], case['grown']]
        assert all(k == 'cpu_reference_wall_seconds' or case.get(k) == now.get(k) for k in set(case) | set(now))
    units = {}
    for name, count in {'unit': 243, 'staged-native': 9, 'source-native': 6, 'native-mode-spec': 4,
                        'native-mode-input': 3, 'reference-rewrite': 3}.items():
        row = next(r for r in gates['gates'] if r['name'] == name)
        text = Path(row['log']).read_text()
        assert f'Ran {count} tests' in text and text.rstrip().endswith('OK')
        units[name] = dict(tests=count, output=text)
    assert len(load('portable-api-metal')['probability_execution']) == 8
    assert len(m['probability_cpu_regressions']) == 92
    assert load('portable-api-metal')['passed'] and len(load('portable-api-metal')['element_override_execution']) == 9
    audit = load('portable-catalog-readiness')
    assert audit['own_effect_preflight_passed'] == 51 and audit['full_character_verified'] == 0
    assert sum(audit['issues'].values()) == 370
    favorite = load('portable-favorite-readiness')
    assert favorite['passed'] and favorite['audited_contexts'] == 812
    assert favorite['stage0_matches_current_audit'] and favorite['own_effect_preflight_contexts_passed'] == 198
    assert favorite['all_four_stages_preflight_characters'] == 49 and not favorite['gpu_execution_performed']
    assert load('portable-range-catalog-native')['native_cases'] == 32886
    for name in ['portable-geometry-layout-study', 'portable-live-range-native',
                 'portable-range-catalog-native', 'portable-favorite-readiness']:
        future = load(name)
        assert future['passed'] and not future['gpu_execution_performed']
        for path, digest in future['source_sha256'].items():
            assert sha((ROOT / path).read_bytes()) == digest, (name, path)
    decision = load('portable-probability-efficiency-decision')
    assert decision['passed'] and decision['selected_for_adoption']
    decision.update(production_change_adopted=True, optimized_source_commit=SOURCE,
                    adoption_stage='Adopted after exact2280-input CUDA/Metal parity and all32 Mac gates',
                    adoption_validation='portable-probability-optimized-validation.json')
    save('portable-probability-efficiency-decision', decision)
    summary = {k: v for k, v in w.items() if k != 'results'}
    (REPORTS / 'portable-combat-cuda.json').write_text(json.dumps(summary, ensure_ascii=False, separators=(',', ':')) + '\n')
    checkpoint = load('portable-combat-checkpoint')
    checkpoint.update(verified_commit=SOURCE, previous_checkpoint=dict(proof_commit=BASELINE,
                      report='Git baseline portable-combat-checkpoint.json'),
                      validation_receipt='portable-probability-optimized-validation.json',
                      windows_report='windows-portable-probability-v68.json', windows_execution=execution,
                      windows_postcheck=post, windows_checks_this_stage=dict(gpu_executions=1, additional_transfer_gpu_runs=0),
                      generated_source_comparison='portable-probability-optimized-validation.json')
    checkpoint['source_provenance'] = dict(fixed_shared_source_commit=SOURCE, metal_core_source_commit=SOURCE,
                                          windows_source_commit=SOURCE, baseline_proof_commit=BASELINE)
    for key in ['source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256', 'batch_layout']:
        checkpoint[key] = m[key]
    checkpoint['existing_parity'] = m['probability_existing_parity']
    save('portable-probability-existing-cuda-parity', w['probability_existing_parity'])
    checkpoint['probability'].update(efficiency=decision, optimized_source_verification_pending=False)
    checkpoint['next_work'] = ['Connect remaining effects/world scheduling;certify all203 characters and all variants',
                               'Keep strict readback capture;initial mismatch is unlocalized and not claimed fixed']
    save('portable-combat-checkpoint', checkpoint)
    paths = [windows_path, receipt_path, 'research/portable-probability-optimized-metal-readback.json',
             'research/portable-probability-optimized-global-gates.json', 'research/portable-probability-efficiency-decision.json',
             'research/portable-combat-checkpoint.json', 'research/portable-combat-cuda.json',
             'research/portable-combat-metal.json', 'research/portable-roster-battles-metal.json']
    current_reports = ['portable-api-metal', 'portable-catalog-readiness', 'portable-catalog-weapons-metal',
                       'portable-real-equipment-metal', 'portable-real-battle-metal', 'portable-events-metal',
                       'portable-numeric-metal', 'portable-probe-metal', 'portable-metal-pipeline-lock',
                       'portable-duration-extend-metal', 'portable-definition-input-metal',
                       'portable-definition-scalar-metal', 'portable-definition-out-metal',
                       'portable-removal-queue-metal', 'portable-stack-numeric-metal', 'portable-stack-notices-metal',
                       'portable-enemy-code-real-metal', 'portable-enemy-codes-native', 'portable-named-states-native',
                       'portable-instant-lists-native', 'portable-protection-native', 'portable-split-native',
                       'portable-element-overrides-native', 'portable-probability-native', 'portable-probability-existing-metal-parity',
                       'portable-probability-existing-cuda-parity']
    paths += ['research/' + name + '.json' for name in current_reports]
    paths += ['research/verify-probability-optimized.py', 'research/run-probability-optimized-gates.py', 'research/seal-probability-optimized.py',
              'research/characterize-probability-values.py', 'research/portable-probability-values-native.json',
              'research/study-report-serialization.py', 'research/portable-report-serialization-study.json',
              'research/portable-probability-optimized-initial-harness-finding.json',
              'research/update-probability-optimized-docs.py']
    paths += ['research/' + name for name in ['study-geometry-layout.py', 'portable-geometry-layout-study.json',
              'characterize-live-range.py', 'portable-live-range-native.json', 'characterize-range-catalog.py',
              'portable-range-catalog-native.json', 'audit-portable-favorites.py', 'portable-favorite-readiness.json',
              'portable-probability-optimized-transfer-completed.json', 'portable-probability-optimized-progress.json']]
    paths += ['docs/' + name + '.md' for name in ['portable-element-overrides', 'mac-handoff', 'mac-migration',
                                                'portable-combat-runtime', 'portable-probability-design']]
    save('portable-probability-optimized-validation', dict(
        passed=True, source_commit=SOURCE, baseline_proof_commit=BASELINE,
        checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), artifact_commit=args.artifact_commit,
        artifact_transfer_complete=True, windows_execution_terminal=True, remaining_verification_processes=0,
        remote_turn=args.remote_turn, remote_turn_status='completed',
        local_verification_processes=processes,
        core_programs=2280, positive_cases=1940, rejections=340, mac_gates=32, unit_tests=243,
        unit_groups=units, real_roster_profiles=102, old_profiles_preserved=102, element_native_cases=156,
        element_api_cases=9, probability_native_cases=92, probability_api_cases=8, compared_keys=keys, normalized_generated_sha256=normalized,
        input_sha256=m['input_sha256'], output_sha256=m['output_sha256'],
        production_change_adopted=True, initial_metal_finding_open=True, root_cause_resolved=False,
        mac_core_gpu_executions_this_stage=2, mac_initial_capture_harness_failures=1,
        windows_core_gpu_executions_this_stage=1, additional_gpu_executions_for_transfer=0,
        full_character_verified=0, full_goal_complete=False, normal_ui_backend='cpu',
        artifact_scope=dict(current='Optimized fixed source;32 gates and full2280 readbacks on both GPUs',
                            historical_baseline='Read baseline artifacts from Git ' + BASELINE,
                            measurement='Existing baseline benchmark selects this exact helper;no new timing run',
                            probability='Expected probability admitted and tested;actual RNG unsupported',
                            future_geometry='CPU-only actual range buffs,203x6 range tables and binary64 boundaries;not GPU admission',
                            favorite_audit='812 CPU-only definition preflights;198 accepted contexts,49 all-stage candidates;not GPU certification',
                            serialization='Lossless compact JSON;Windows artifact byte-exact'),
        artifact_sha256={p: sha((ROOT / p).read_bytes()) for p in sorted(set(paths))}))
    print('Optimized shared source: all2280 CUDA/Metal outputs and32 Mac gates pass; initial finding remains open')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote-turn', required=True)
    parser.add_argument('--artifact-commit', required=True)
    parser.add_argument('--windows-sha256', required=True)
    parser.add_argument('--readback-sha256', required=True)
    main(parser.parse_args())
