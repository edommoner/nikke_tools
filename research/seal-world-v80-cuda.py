"""CPU-only seal of imported phase evidence and exact CUDA/Metal fingerprints."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '86f66858e24f051fe3a617ddb13661adc5af9614'

def load(name):
    return json.loads((ROOT/'research'/name).read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    expected_path = ROOT/'research/portable-cross-v79-expected.json'
    expected = json.loads(expected_path.read_text())
    summary = load('windows-portable-cross-v80c-summary.json')
    execution = load('portable-cross-v80c-execution.json')
    assert summary['passed'] and not summary['changed_keys'] and summary['backend'] == 'cuda'
    assert summary['source_commit'] == execution['source_commit'] == SOURCE
    assert summary['expected_sha256'] == sha(expected_path)
    assert summary['comparison'] == expected['comparison']
    facts = summary['observed']
    assert facts['core_passed'] and facts['world_passed']
    assert facts['positive_cases'] == 4112 and facts['negative_cases'] == 570 and facts['world_cases'] == 49
    assert facts['core_gpu_execution_verified'] and facts['world_gpu_execution_verified']
    assert facts['core_report_source_commit'] == '6f54193636f2e44e59a588e208528f099419ac6e'
    assert facts['world_report_source_commit'] == SOURCE
    for transport in (facts['core_transport'], facts['world_transport']):
        assert transport['backend'] == 'cuda' and transport['command_status'] == 'completed'
    payload = load('portable-world-v80-source-payload.json')
    rows = {r['path']: dict(bytes=r['bytes'], sha256=r['sha256']) for r in payload['rows']}
    assert execution['preflight_five_files'] == rows and payload['commit'] == SOURCE
    for path, row in rows.items():
        raw = subprocess.check_output(['git', 'show', SOURCE+':'+path], cwd=ROOT)
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    subprocess.run(['git', 'diff', '--exit-code', payload['parent'], SOURCE, '--',
                    'app', 'gpu', 'scripts', 'research/verify-world-suite.py',
                    'research/portable-cross-v79-expected.json', 'research/summarize-portable-cross-gpu.py'], cwd=ROOT, check=True)
    cpu = load('portable-cross-v80-cpu-environment.json')
    imports = load('portable-cross-v80-import-preflight.json')
    assert execution['cpu_environment_reference_sha256'] == sha(ROOT/'research/portable-cross-v80-cpu-environment.json')
    assert execution['import_preflight_sha256'] == sha(ROOT/'research/portable-cross-v80-import-preflight.json')
    assert cpu['cpu_environment_retest']['exit_code'] == 0 and cpu['job_object_descendant_termination_verified']
    assert cpu['original_log_unchanged'] and cpu['actual_gpu_execution_count'] == 0
    assert imports['passed'] and imports['expected_equal'] and imports['sentinel_call_count'] == 0
    assert imports['input_sha256'] == expected['comparison']['world_input_sha256']
    run = execution['runner_execution']
    assert run['passed'] and not run['timed_out'] and run['child_exit_code'] == run['final_child_exit_code'] == 0
    assert run['timeout_seconds'] == 180 and run['cleanup_wait_seconds'] == 5 and run['below_normal_priority']
    assert run['error'] is None and run['cleanup_error'] is None and run['gpu_retry_count'] == 0
    assert execution['actual_world_gpu_execution_count'] == 1 and execution['actual_core_gpu_execution_count'] == 0
    assert execution['saved_core_reused'] and execution['no_gpu_retry']
    assert execution['original_head_equal'] and execution['original_status_equal']
    assert execution['existing_gpu_service_preserved'] and execution['residual_verification_process_count'] == 0
    assert execution['runner_manifest']['gpu_source_sha256'] == expected['comparison']['world_source_sha256']
    phases = execution['phases']
    assert len(phases) == 50 and len({r['pid'] for r in phases}) == 1
    assert all(a['monotonic_ns'] <= b['monotonic_ns'] for a, b in zip(phases, phases[1:]))
    ordered = []
    for stage in ('nvrtcCompileProgram', 'cuLaunchKernel', 'cuCtxSynchronize', 'cuMemcpyDtoH_v2'):
        entered = [i for i, r in enumerate(phases) if r['stage'] == stage and r['state'] == 'entered']
        returned = [i for i, r in enumerate(phases) if r['stage'] == stage and r['state'] == 'returned' and r.get('return_code') == 0]
        assert len(entered) == len(returned) == 1 and entered[0] < returned[0]
        ordered.extend([entered[0], returned[0]])
    assert ordered == sorted(ordered)
    names = ['windows-portable-cross-v80-summary.json', 'portable-cross-v80-execution.json',
             'portable-cross-v80-cpu-environment.json', 'windows-portable-cross-v80b-summary.json',
             'portable-cross-v80b-execution.json', 'portable-cross-v80-import-preflight.json',
             'windows-portable-cross-v80c-summary.json', 'portable-cross-v80c-execution.json']
    receipt = dict(passed=True, source_commit=SOURCE,
                   artifacts={n: dict(bytes=(ROOT/'research'/n).stat().st_size, sha256=sha(ROOT/'research'/n)) for n in names},
                   normal_core_inputs=4682, normal_core_gpu_runs_this_phase=0, normal_core_saved_v79_reused=True,
                   world_inputs=49, world_gpu_runs=1, world_elapsed_seconds=run['elapsed_seconds'],
                   all_input_output_native_source_and_generated_fingerprints_equal=True,
                   nvrtc_launch_sync_readback_observed_success=True,
                   original_cpu_temp_and_import_failures_retained=True, gpu_retries=0,
                   windows_execution_and_transfer_terminal=True, residual_verification_process_count=0,
                   normal_ui='CPU', full_character_verified=0, full_goal_complete=False,
                   scope='Shared frame/target/attack/closed-notice world49 and saved normal4682. This does not certify new ABI75 overlays,actors or the complete catalog.',
                   updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (ROOT/'research/portable-world-v80-cuda-validation.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('CUDA world49 and saved normal4682 exactly match Metal; actual native API phases verified')

if __name__ == '__main__':
    main()
