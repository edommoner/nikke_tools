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
SOURCE = '32653b09d597f0443c0df11f2076b249ec33dbd7'
BASELINE = '80170c3b922b666eadb1f72bec22331c183a89b4'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())


def save(name, value):
    (REPORTS / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(args):
    gates = load('portable-element-optimized-global-gates')
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 31
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
    windows_path = 'research/windows-portable-element-v66.json'
    receipt_path = 'research/portable-element-optimized-cuda-readback.json'
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
    w = load('windows-portable-element-v66')
    assert m['passed'] and w['passed'] and m['gpu_execution_verified'] and w['gpu_execution_verified']
    assert m['backend'] == 'metal' and w['backend'] == 'cuda'
    assert len(m['cases']) == 1848 and len(m['rejected_cases']) == 334
    assert len(m['element_override_cpu_regressions']) == 156
    keys = ['source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256',
            'actual_statuses', 'expected_statuses', 'batch_layout', 'rejected_cases', 'cases']
    keys += [key for key in m if key.endswith('_cpu_regressions') or key.startswith('known_')]
    for key in keys:
        assert m[key] == w[key], key
    for path in ['research/verify-element-optimized.py', 'research/verify-element-regression.py',
                 'research/run-element-gates-optimized.py']:
        assert (ROOT / path).read_bytes() == git_bytes(SOURCE, path), path
    parity = m['element_override_existing_parity']
    assert parity['passed'] and parity['all_old_output_words_equal'] and parity['no_output_normalization']
    assert parity['prior_inputs'] == 2006 and parity['current_inputs'] == 2182
    assert parity['driver_sha256'] == sha((REPORTS / 'verify-element-regression.py').read_bytes())
    for key in parity:
        if key != 'actual_dispatch_counts':
            assert parity[key] == w['element_override_existing_parity'][key], key
    baseline_manifest = json.loads(git_bytes(BASELINE, 'research/portable-element-baseline-output-blocks.json'))
    for backend in ['metal', 'cuda']:
        receipt = load('portable-element-optimized-' + backend + '-readback')
        assert receipt['passed'] and receipt['source_commit'] == SOURCE
        assert receipt['input_equal'] and receipt['output_equal'] and not receipt['changed']
        assert receipt['programs'] == 2182 and receipt['baseline_proof_commit'] == BASELINE
        assert receipt['no_gpu_retry'] and receipt['no_output_normalization']
        assert receipt['evidence']['input_sha256'] == baseline_manifest['input_sha256'] == m['input_sha256']
        assert receipt['evidence']['output_sha256'] == baseline_manifest['output_sha256'] == m['output_sha256']
        assert receipt['actual_block_sha256'] == [b['sha256'] for b in baseline_manifest['blocks']]
        assert receipt['capture_tool_sha256'] == sha((REPORTS / 'verify-element-optimized.py').read_bytes())
    for group in ['source_sha256', 'validation_sha256']:
        for path, expected in m[group].items():
            assert sha((ROOT / path).read_bytes()) == sha(git_bytes(SOURCE, path)) == expected, path
    candidate = load('portable-element-candidate-parity')
    candidate_key = 'research/portable-build/element-accessors/gpu/element_runtime.slang'
    assert sha((ROOT / 'gpu/element_runtime.slang').read_bytes()) == candidate['parity']['accessors']['source_sha256'][candidate_key]
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
    assert roster['passed'] and len(roster['cases']) == 86
    assert len(old_roster['cases']) == 86
    lookup = {(c['character'], c['grown']): c for c in roster['cases']}
    for case in old_roster['cases']:
        now = lookup[case['character'], case['grown']]
        assert all(k == 'cpu_reference_wall_seconds' or case.get(k) == now.get(k) for k in set(case) | set(now))
    units = {}
    for name, count in {'unit': 237, 'staged-native': 9, 'source-native': 6, 'native-mode-spec': 4,
                        'native-mode-input': 3, 'reference-rewrite': 3}.items():
        row = next(r for r in gates['gates'] if r['name'] == name)
        text = Path(row['log']).read_text()
        assert f'Ran {count} tests' in text and text.rstrip().endswith('OK')
        units[name] = dict(tests=count, output=text)
    assert load('portable-api-metal')['passed'] and len(load('portable-api-metal')['element_override_execution']) == 9
    audit = load('portable-catalog-readiness')
    assert audit['own_effect_preflight_passed'] == 43 and audit['full_character_verified'] == 0
    assert sum(audit['issues'].values()) == 384
    decision = load('portable-element-efficiency-decision')
    assert decision['passed'] and decision['selected_for_adoption']
    decision.update(production_change_adopted=True, optimized_source_commit=SOURCE,
                    adoption_stage='Adopted after exact2182-input CUDA/Metal parity and all31 Mac gates',
                    adoption_validation='portable-element-optimized-validation.json')
    save('portable-element-efficiency-decision', decision)
    save('portable-combat-cuda', dict(w, summary_only=True, summary_source='windows-portable-element-v66.json'))
    checkpoint = load('portable-combat-checkpoint')
    checkpoint.update(verified_commit=SOURCE, previous_checkpoint=dict(proof_commit=BASELINE,
                      report='Git baseline portable-combat-checkpoint.json'),
                      validation_receipt='portable-element-optimized-validation.json',
                      windows_report='windows-portable-element-v66.json', windows_execution=execution,
                      windows_postcheck=post, windows_checks_this_stage=2,
                      generated_source_comparison='portable-element-optimized-validation.json')
    checkpoint['source_provenance'] = dict(fixed_shared_source_commit=SOURCE, metal_core_source_commit=SOURCE,
                                          windows_source_commit=SOURCE, baseline_proof_commit=BASELINE)
    for key in ['source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256', 'batch_layout']:
        checkpoint[key] = m[key]
    checkpoint['element_overrides'].update(efficiency=decision, optimized_source_verification_pending=False)
    checkpoint['next_work'] = ['Connect probability and remaining effects/world scheduling;certify all203 characters and all variants',
                               'Keep strict readback capture;initial mismatch is unlocalized and not claimed fixed']
    save('portable-combat-checkpoint', checkpoint)
    paths = [windows_path, receipt_path, 'research/portable-element-optimized-metal-readback.json',
             'research/portable-element-optimized-global-gates.json', 'research/portable-element-efficiency-decision.json',
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
                       'portable-element-overrides-native', 'portable-element-existing-metal-parity']
    paths += ['research/' + name + '.json' for name in current_reports]
    paths += ['research/verify-element-optimized.py', 'research/run-element-gates-optimized.py', 'research/seal-element-optimized.py',
              'research/characterize-probability-values.py', 'research/portable-probability-values-native.json',
              'research/study-report-serialization.py', 'research/portable-report-serialization-study.json',
              'research/update-element-optimized-docs.py']
    paths += ['docs/' + name + '.md' for name in ['portable-element-overrides', 'mac-handoff', 'mac-migration',
                                                'portable-combat-runtime', 'portable-probability-design']]
    save('portable-element-optimized-validation', dict(
        passed=True, source_commit=SOURCE, baseline_proof_commit=BASELINE,
        checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), artifact_commit=args.artifact_commit,
        artifact_transfer_complete=True, windows_execution_terminal=True, remaining_verification_processes=0,
        remote_turn='01a1576d-c2df-7d90-b033-3fc3a6bba20b', remote_turn_status='completed',
        local_verification_processes=processes,
        core_programs=2182, positive_cases=1848, rejections=334, mac_gates=31, unit_tests=237,
        unit_groups=units, real_roster_profiles=86, old_profiles_preserved=86, element_native_cases=156,
        element_api_cases=9, compared_keys=keys, normalized_generated_sha256=normalized,
        input_sha256=m['input_sha256'], output_sha256=m['output_sha256'],
        production_change_adopted=True, initial_metal_finding_open=True, root_cause_resolved=False,
        full_character_verified=0, full_goal_complete=False, normal_ui_backend='cpu',
        artifact_scope=dict(current='Optimized fixed source;31 gates and full2182 readbacks on both GPUs',
                            historical_baseline='Read baseline artifacts from Git ' + BASELINE,
                            measurement='Existing baseline benchmark selects this exact helper;no new timing run',
                            probability='CPU-only characterization and proposed design;GPU admission disabled',
                            serialization='Offline lossless size experiment;production report format unchanged'),
        artifact_sha256={p: sha((ROOT / p).read_bytes()) for p in sorted(set(paths))}))
    print('Optimized shared source: all2182 CUDA/Metal outputs and31 Mac gates pass; initial finding remains open')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifact-commit', required=True)
    parser.add_argument('--windows-sha256', required=True)
    parser.add_argument('--readback-sha256', required=True)
    main(parser.parse_args())
