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
SOURCE = '7492d8b191471f820989dc760bc4adc91494cf6a'
CUDA_CORE_SOURCE = '5a3ee26039dc031f98ccd34a9c3245ff606a8808'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())


def save(name, value):
    (REPORTS / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


def main(args):
    m, w = load('portable-combat-metal'), load('windows-portable-attack-flags-v72')
    assert m['passed'] and w['passed'] and m['backend'] == 'metal' and w['backend'] == 'cuda'
    assert m['gpu_execution_verified'] and w['gpu_execution_verified']
    paths = ['research/windows-portable-attack-flags-v72.json', 'research/portable-attack-flags-existing-cuda-parity.json']
    expected = [args.windows_sha256, args.parity_sha256]
    changed = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', args.artifact_commit], cwd=ROOT, text=True).splitlines()
    assert changed == sorted(paths)
    assert subprocess.check_output(['git', 'rev-parse', args.artifact_commit + '^'], cwd=ROOT, text=True).strip() == CUDA_CORE_SOURCE
    for path, digest in zip(paths, expected):
        data = (ROOT / path).read_bytes()
        assert sha(data) == digest and data == git_bytes(args.artifact_commit, path), path
    metadata=load('portable-attack-flags-windows-execution')
    assert metadata['passed'] and metadata['source_commit']==CUDA_CORE_SOURCE and metadata['actual_gpu_execution_count']==1
    execution, post = metadata['execution'], metadata
    assert execution['commit'] == CUDA_CORE_SOURCE and execution['exit_code'] == 0 and not execution['timed_out']
    assert execution['below_normal_priority'] and execution['timeout_seconds'] == 120
    assert post['residual_verification_process_count'] == 0
    assert post['existing_gpu_service_preserved']
    assert post['original_head_equal'] and post['original_status_equal']
    keys = ['source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256', 'cases', 'rejected_cases',
            'actual_statuses', 'expected_statuses', 'batch_layout']
    keys += [k for k in m if k.endswith('_cpu_regressions') or k.startswith('known_')]
    for key in keys:
        assert m[key] == w[key], key
    assert len(m['cases']) == 2525 and len(m['rejected_cases']) == 425 and len(m['probability_cpu_regressions']) == 92 and len(m['geometry_cpu_regressions']) == 190 and len(m['target_state_cpu_regressions']) == 233 and len(m['attack_flag_cpu_regressions']) == 162
    for group in ['source_sha256', 'validation_sha256']:
        for path, digest in m[group].items():
            assert sha((ROOT / path).read_bytes()) == sha(git_bytes(SOURCE, path)) == sha(git_bytes(CUDA_CORE_SOURCE,path)) == digest, path
    for backend, report in [('metal', m), ('cuda', w)]:
        parity = report['attack_flag_existing_parity']
        external = load('portable-attack-flags-existing-' + backend + '-parity')
        assert parity == external and parity['passed'] and parity['source_commit'] == (SOURCE if backend=='metal' else CUDA_CORE_SOURCE)
        assert parity['compute_worktree_clean'] and not parity['gpu_execution_reused'] and not parity['changed']
        assert parity['prior_inputs'] == 2754 and parity['current_inputs'] == 2950
        assert parity['all_old_output_words_equal'] and parity['no_gpu_retry'] and parity['no_output_normalization']
        assert parity['driver_sha256'] == sha(git_bytes(SOURCE, 'research/verify-attack-flags-regression.py'))
    for key in m['attack_flag_existing_parity']:
        if key not in ['evidence', 'input_path', 'raw_path', 'source_commit']:
            assert m['attack_flag_existing_parity'][key] == w['attack_flag_existing_parity'][key], key
    spec = importlib.util.spec_from_file_location('normalizer', REPORTS / 'seal-stack-increment.py')
    helper = importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    normalized = {}
    for backend, suffix in [('cuda', 'cu'), ('metal', 'metal')]:
        data = (REPORTS / 'portable-build' / ('event_runtime.' + suffix)).read_bytes()
        assert sha(data) == m['generated_sha256'][backend]
        normalized[backend] = helper.normalized(data)
        assert normalized[backend] == metadata['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
    hp_m=load('portable-health-runtime-metal');hp_w=load('windows-portable-health-runtime-v73')
    hp_execution=load('portable-health-runtime-v73-execution')
    assert hp_m['passed'] and hp_w['passed'] and hp_m['backend']=='metal' and hp_w['backend']=='cuda'
    assert hp_m['gpu_execution_verified'] and hp_w['gpu_execution_verified'] and len(hp_m['cases'])==20
    for key in ['input_sha256','output_sha256','source_sha256','validation_sha256','cases']:
        assert hp_m[key]==hp_w[key],key
    for path,digest in hp_m['validation_sha256'].items():
        assert sha((ROOT/path).read_bytes())==digest,path
        if subprocess.run(['git','ls-files','--error-unmatch',path],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
            assert sha(git_bytes(SOURCE,path))==digest,path
    assert hp_execution['source_commit']==SOURCE and hp_execution['actual_gpu_execution_count']==1
    hp_run=hp_execution['execution']
    assert hp_run['commit']==SOURCE and hp_run['exit_code']==0 and not hp_run['timed_out']
    assert hp_run['below_normal_priority'] and hp_run['timeout_seconds']==120
    assert hp_execution['original_head_equal'] and hp_execution['original_status_equal']
    assert hp_execution['residual_verification_process_count']==0 and hp_execution['existing_gpu_service_preserved']
    for backend in ('cuda','metal'):
        assert hp_execution['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']==normalized[backend]
    hp_artifact=args.hp_artifact_commit
    hp_paths=['research/windows-portable-health-runtime-v73.json','research/portable-health-runtime-v73-execution.json']
    assert subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',hp_artifact],cwd=ROOT,text=True).splitlines()==sorted(hp_paths)
    assert subprocess.check_output(['git','rev-parse',hp_artifact+'^'],cwd=ROOT,text=True).strip()==SOURCE
    for path,digest in zip(hp_paths,[args.hp_report_sha256,args.hp_execution_sha256]):
        data=(ROOT/path).read_bytes();assert sha(data)==digest and data==git_bytes(hp_artifact,path)
    transfer = dict(passed=True, source_commit=SOURCE, artifact_commit=args.artifact_commit,
                    conditional_hp_component_cases=20,conditional_hp_source_commit=SOURCE,
                    conditional_hp_artifact_commit=hp_artifact,conditional_hp_execution=hp_run,
                    core_cuda_verification_mode='All2950 source/input-identical results retained fromv72;20 additional HP contract inputs freshly executed at current source',
                    retained_cuda_core_source_commit=CUDA_CORE_SOURCE,core_gpu_and_validation_source_bytes_equal=True, current_source_full_cuda_core_freshly_executed=False, windows_execution_metadata_report='portable-attack-flags-windows-execution.json', windows_report=paths[0], windows_report_sha256=expected[0], parity_report_sha256=expected[1],
                    checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), artifact_transfer_complete=True,
                    core_artifact_remote_turn='01a15831-7722-7621-8caf-8f02d6692151',additional_component_artifact_remote_turn=args.remote_turn,remote_turn_status='completed', windows_execution_terminal=True,
                    remaining_verification_processes=0, core_programs=2950, attack_flag_native_cases=162, target_state_native_cases=233, geometry_native_cases=190, probability_native_cases=92,
                    positive_cases=2525, rejections=425, compared_keys=keys, normalized_generated_sha256=normalized,
                    input_sha256=m['input_sha256'], output_sha256=m['output_sha256'],
                    cuda_dispatch_counts=[d['transport']['cases'] for d in w['dispatches']],
                    metal_dispatch_counts=[d['transport']['cases'] for d in m['dispatches']],
                    initial_unlocalized_metal_finding_open=True, full_goal_complete=False)
    save('portable-attack-flags-transfer-completed', transfer)
    if args.timing_order:
        broad = load('portable-attack-flags-broad-validation')
        assert broad['passed'] and broad['all_current_gates_passed'] and broad['source_commit'] == SOURCE and broad['mac_gates'] == 37
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
        assert not (REPORTS / 'portable-attack-flags-timing-order.json').exists()
        save('portable-attack-flags-timing-order', dict(passed=True, source_commit=SOURCE,
             checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), mac_gates=37,
             all_current_mac_gates_complete=True, windows_execution_and_transfer_terminal=True,
             verification_processes=processes, transfer=transfer, initial_unlocalized_metal_finding_open=True))
    print('2950 source/input-identical retained CUDA core results and20 fresh HP inputs agree with current Metal;transfers verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifact-commit', required=True)
    parser.add_argument('--windows-sha256', required=True)
    parser.add_argument('--parity-sha256', required=True)
    parser.add_argument('--remote-turn', required=True)
    parser.add_argument('--timing-order', action='store_true')
    parser.add_argument('--hp-artifact-commit',required=True)
    parser.add_argument('--hp-report-sha256',required=True)
    parser.add_argument('--hp-execution-sha256',required=True)
    main(parser.parse_args())
