"""Verify a terminal short CUDA run and its two Git-transferred report blobs."""
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
SOURCE = '17decef851fbea0a300e16706c63ff6702e6e83f'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())


def save(name, value):
    (REPORTS / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


def main(args):
    m, w = load('portable-combat-metal'), load('windows-portable-geometry-v69')
    assert m['passed'] and w['passed'] and m['backend'] == 'metal' and w['backend'] == 'cuda'
    assert m['gpu_execution_verified'] and w['gpu_execution_verified']
    paths = ['research/windows-portable-geometry-v69.json', 'research/portable-geometry-existing-cuda-parity.json']
    expected = [args.windows_sha256, args.parity_sha256]
    changed = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', args.artifact_commit], cwd=ROOT, text=True).splitlines()
    assert changed == sorted(paths)
    assert subprocess.check_output(['git', 'rev-parse', args.artifact_commit + '^'], cwd=ROOT, text=True).strip() == SOURCE
    for path, digest in zip(paths, expected):
        data = (ROOT / path).read_bytes()
        assert sha(data) == digest and data == git_bytes(args.artifact_commit, path), path
    execution, post = w['execution'], w['postcheck']
    assert execution['commit'] == SOURCE and execution['exit_code'] == 0 and not execution['timed_out']
    assert execution['below_normal_priority'] and execution['timeout_seconds'] == 120
    assert post['residual_verification_process_count'] == 0 and not post['residual_verification_processes']
    assert post['existing_gpu_service_preserved']
    for field in ['head', 'status']:
        assert execution['original_' + field + '_before'] == post['original_' + field + '_after']
    keys = ['source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256', 'cases', 'rejected_cases',
            'actual_statuses', 'expected_statuses', 'batch_layout']
    keys += [k for k in m if k.endswith('_cpu_regressions') or k.startswith('known_')]
    for key in keys:
        assert m[key] == w[key], key
    assert len(m['cases']) == 2130 and len(m['rejected_cases']) == 373 and len(m['probability_cpu_regressions']) == 92 and len(m['geometry_cpu_regressions']) == 190
    for group in ['source_sha256', 'validation_sha256']:
        for path, digest in m[group].items():
            assert sha((ROOT / path).read_bytes()) == sha(git_bytes(SOURCE, path)) == digest, path
    for backend, report in [('metal', m), ('cuda', w)]:
        parity = report['geometry_existing_parity']
        external = load('portable-geometry-existing-' + backend + '-parity')
        assert parity == external and parity['passed'] and parity['source_commit'] == SOURCE
        assert parity['compute_worktree_clean'] and not parity['gpu_execution_reused'] and not parity['changed']
        assert parity['prior_inputs'] == 2280 and parity['current_inputs'] == 2503
        assert parity['all_old_output_words_equal'] and parity['no_gpu_retry'] and parity['no_output_normalization']
        assert parity['driver_sha256'] == sha(git_bytes(SOURCE, 'research/verify-geometry-regression.py'))
    for key in m['geometry_existing_parity']:
        if key not in ['evidence', 'input_path', 'raw_path']:
            assert m['geometry_existing_parity'][key] == w['geometry_existing_parity'][key], key
    spec = importlib.util.spec_from_file_location('normalizer', REPORTS / 'seal-stack-increment.py')
    helper = importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    normalized = {}
    for backend, suffix in [('cuda', 'cu'), ('metal', 'metal')]:
        data = (REPORTS / 'portable-build' / ('event_runtime.' + suffix)).read_bytes()
        assert sha(data) == m['generated_sha256'][backend]
        normalized[backend] = helper.normalized(data)
        assert normalized[backend] == w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
    transfer = dict(passed=True, source_commit=SOURCE, artifact_commit=args.artifact_commit,
                    windows_report=paths[0], windows_report_sha256=expected[0], parity_report_sha256=expected[1],
                    checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), artifact_transfer_complete=True,
                    remote_turn=args.remote_turn, remote_turn_status='completed', windows_execution_terminal=True,
                    remaining_verification_processes=0, core_programs=2503, geometry_native_cases=190, probability_native_cases=92,
                    positive_cases=2130, rejections=373, compared_keys=keys, normalized_generated_sha256=normalized,
                    input_sha256=m['input_sha256'], output_sha256=m['output_sha256'],
                    cuda_dispatch_counts=[d['transport']['cases'] for d in w['dispatches']],
                    metal_dispatch_counts=[d['transport']['cases'] for d in m['dispatches']],
                    initial_unlocalized_metal_finding_open=True, full_goal_complete=False)
    save('portable-geometry-transfer-completed', transfer)
    if args.timing_order:
        broad = load('portable-geometry-broad-validation')
        assert broad['passed'] and broad['all_current_gates_passed'] and broad['source_commit'] == SOURCE and broad['mac_gates'] == 34
        subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=ROOT, check=True)
        processes = []
        for line in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,etime=,command='], text=True).splitlines():
            parts = line.split(None, 3)
            if len(parts) != 4:
                continue
            pid, ppid, elapsed, command = parts
            if int(pid) == os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh', '/bin/bash')):
                continue
            if any(x in command for x in [' research/run-', ' research/verify-', ' scripts/verify-portable-', '/scripts/run-metal-probe.swift', ' research/benchmark-', ' research/capture-']):
                processes.append(dict(pid=int(pid), ppid=int(ppid), elapsed=elapsed, command=command))
        assert not processes, processes
        assert not (REPORTS / 'portable-geometry-timing-order.json').exists()
        save('portable-geometry-timing-order', dict(passed=True, source_commit=SOURCE,
             checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), mac_gates=34,
             all_current_mac_gates_complete=True, windows_execution_and_transfer_terminal=True,
             verification_processes=processes, transfer=transfer, initial_unlocalized_metal_finding_open=True))
    print('Full2503-input CUDA/Metal source,input,output,status,native and saved-transfer parity verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifact-commit', required=True)
    parser.add_argument('--windows-sha256', required=True)
    parser.add_argument('--parity-sha256', required=True)
    parser.add_argument('--remote-turn', required=True)
    parser.add_argument('--timing-order', action='store_true')
    main(parser.parse_args())
