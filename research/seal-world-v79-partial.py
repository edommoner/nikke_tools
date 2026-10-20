"""CPU-only receipt for a successful normal core and incomplete world run."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '6f54193636f2e44e59a588e208528f099419ac6e'
ARTIFACTS = {
    'windows-portable-cross-v79-summary.json': (1946, '3e2cbb4c5f5cfa9eb778ed82baaed5554584f87ef0c258695f9c71ef3316fb32'),
    'portable-cross-v79-execution.json': (3771, '9674201eba526349cce473da35e3d9ee164ba573af1e0ca2f03129b142f5551f'),
    'windows-portable-cross-v79-core-summary.json': (36136, 'cc0bd4903902959c898dafaa8bc7ef4849aac448472d46f7af1f484d7aac8caf'),
    'portable-cross-v79-phase-diagnostics.json': (5904, '7a2fbbfbb3f8cad253d6b452a439ca1f998f4c2b616347b7a87bbb3c6968d554'),
}

def load(name):
    return json.loads((ROOT/'research'/name).read_text())

def main():
    for name, (size, sha) in ARTIFACTS.items():
        raw = (ROOT/'research'/name).read_bytes()
        assert len(raw) == size and hashlib.sha256(raw).hexdigest() == sha, name
        assert json.loads(raw)['source_commit'] == SOURCE, name
    core = load('windows-portable-cross-v79-core-summary.json')
    expected_path = ROOT/'research/portable-cross-v79-expected.json'
    expected = json.loads(expected_path.read_text())['comparison']
    assert hashlib.sha256(expected_path.read_bytes()).hexdigest() == core['expected_report_sha256']
    keys = {'core_input_sha256', 'core_output_sha256', 'core_source_sha256',
            'core_validation_sha256', 'core_semantic_fields', 'core_existing_parity',
            'generated_normalized_sha256'}
    assert set(core['comparison']) == keys
    for key in keys:
        reference = {'core': expected[key]['core']} if key == 'generated_normalized_sha256' else expected[key]
        assert core['comparison'][key] == reference, key
    assert core['passed'] and core['cpu_only'] and not core['world_verified']
    assert core['gpu_reexecutions'] == 0 and not core['changed_keys']
    execution = load('portable-cross-v79-execution.json')
    phase = load('portable-cross-v79-phase-diagnostics.json')
    assert execution['steps'][0]['exit_code'] == 0 and execution['core_gpu_calls'] == 1
    assert execution['execution']['timed_out'] and execution['execution']['elapsed_seconds'] is None
    assert execution['execution']['timeout_seconds'] == 180 and execution['retry_count'] == 0
    assert execution['execution']['below_normal_priority']
    assert execution['original_head_equal'] and execution['original_status_equal']
    assert execution['existing_gpu_service_preserved'] and execution['residual_verification_process_count'] == 0
    assert phase['cpu_only'] and phase['gpu_reexecutions'] == 0 and not phase['world_verified']
    assert phase['world_stage']['gpu_submitted'] == 'unknown'
    assert not phase['world_stage']['readback_saved'] and not phase['world_stage']['evidence_saved']
    assert phase['residual_verification_process_count'] == 0
    assert phase['world_stage']['input_saved']
    saved_input = next(x for x in phase['file_observations'] if x.get('sha256') == expected['world_input_sha256'])
    assert saved_input['bytes'] == 17414212
    receipt = dict(passed=True, source_commit=SOURCE, cpu_only=True,
                   artifacts=[dict(name='research/'+n, bytes=s, sha256=h) for n, (s, h) in ARTIFACTS.items()],
                   core_inputs=4682, core_full_fingerprint_equal=True,
                   core_elapsed_seconds=execution['steps'][0]['elapsed_seconds'],
                   world_input_equal=True, world_verified=False, world_gpu_submitted='unknown',
                   whole_cuda_validation_passed=False, timeout_elapsed_seconds=None,
                   remote_jobs_terminal=True, transferred_via_authorized_existing_connection=True,
                   gpu_reexecutions=0, efficiency_started=False, normal_ui='CPU',
                   full_character_verified=0, full_goal_complete=False,
                   scope='Integrity and complete normal-core fingerprint passed. World CUDA remains incomplete; no timeout stage or successful world execution is inferred.',
                   updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (ROOT/'research/portable-cross-v79-partial-validation.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('Core4682 exact; world input exact, CUDA execution unverified; four transfers verified, no GPU retry')

if __name__ == '__main__':
    main()
