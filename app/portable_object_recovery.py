"""Read-only recovery of a completed module tool under a timed-out packet.

The original incomplete capture stays incomplete. A separate receipt anchors
its bytes and invokes the existing object auditor, never another native tool.
"""
from pathlib import Path

MISSING = ('artifacts.json', 'result.json', 'failure.json')


def snapshot(cli, package, capture):
    outer = capture.parent
    result = {}
    for label, folder in (('outer', outer), ('proof', capture)):
        names = []
        for path in folder.iterdir():
            if path.is_symlink():
                raise ValueError('Recovery rejects capture symlinks')
            if path.is_file():
                names.append(path.name)
        result[label] = cli.file_records(folder, names)
    result['package'] = cli.file_records(package, ['gpu-package.json',
        'module-object-claimed-cuda.json', 'packet-stage-claimed-module-object-cuda.json'])
    return result


def verify_terminal_timeout(cli, capture):
    """Shared terminal outer-timeout / successful inner Job admission."""
    outer = capture.parent
    facts = cli.load(outer / 'execution.json')
    inner = cli.load(capture / 'execution.json')
    if (facts.get('timed_out') is not True or facts.get('passed') is not False
        or inner.get('timed_out') is not False or inner.get('child_exit_code') != 0
        or inner.get('passed') is not True):
        raise ValueError('Recovery requires a terminal outer timeout and successful inner tool')
    for value in (facts, inner):
        if (value.get('cleanup_error') is not None or value.get('observation_error') is not None
            or value.get('below_normal_priority') is not True):
            raise ValueError('Recovery cleanup, observation or priority unverified')
    jobs = cli.load(outer / 'job.json')['records']
    if len(jobs) != 1:
        raise ValueError('Recovery requires one outer Job')
    job = jobs[0]; pre = job['pre_gate']; post = job['post_wait']
    if (job.get('pre_gate_verified') is not True or job.get('inspection_error') is not None
        or pre['child_pid'] != post['child_pid'] or pre['child_pid'] != job['child_pid']
        or pre['child_ppid'] != post['child_ppid'] or pre['child_ppid'] != job['wrapper_pid']
        or pre['job_members'] != [job['child_pid']] or post['job_members'] != []
        or not pre['child_creation_filetime_ticks']
        or pre['child_creation_filetime_ticks'] != post['child_creation_filetime_ticks']
        or pre['job_memory_limit_bytes'] != 2147483648 or post['job_memory_limit_bytes'] != 2147483648):
        raise ValueError('Recovery outer Job not closed or not contained')
    from windows_validation_observer import compare_snapshots
    observation = cli.load(outer / 'observation.json')
    comparison = compare_snapshots(observation['before'], observation['after'])
    if observation['comparison'] != comparison or comparison['missing_existing_processes']:
        raise ValueError('Recovery outer observation mismatch or missing process')


def verify_original(cli, package, capture):
    package = Path(package).resolve(); capture = Path(capture).resolve()
    outer = capture.parent
    manifest = cli.verify_package(package, historical_compiler=True)
    run = cli.load(capture / 'run.json')
    if run.get('package_id') != manifest['package_id'] or run.get('status') != 'processing':
        raise ValueError('Recovery requires the original incomplete module capture')
    if any((capture / name).exists() for name in MISSING):
        raise ValueError('Recovery does not replace an existing result or artifact list')
    plan = cli.load(outer / 'recipe.json')
    packet = cli.module(cli.ROOT / 'scripts/run-gpu-packet.py')
    expected = packet.recipe(manifest['package_id'], 'module-object', 'cuda', outer,
        plan['original_workspace'], plan['timeout_seconds'], plan['object_request'])
    if plan != expected or Path(plan['proof_capture']).resolve() != capture:
        raise ValueError('Recovery packet recipe mismatch')
    verify_terminal_timeout(cli, capture)
    request = cli.load(capture / 'object-request.json')
    original_request = {key: request[key] for key in plan['object_request']}
    if original_request != plan['object_request'] or request.get('source_kind') != 'module':
        raise ValueError('Recovery original request mismatch')
    claim = cli.load(package / 'module-object-claimed-cuda.json')
    packet_claim = cli.load(package / 'packet-stage-claimed-module-object-cuda.json')
    if (claim.get('package_id') != manifest['package_id'] or Path(claim['capture']).resolve() != capture
        or claim.get('origin') != request.get('origin')
        or packet_claim.get('package_id') != manifest['package_id']
        or Path(packet_claim['capture']).resolve() != outer):
        raise ValueError('Recovery consumed claim mismatch')
    return manifest


def recover(cli, package, capture, output, expected_object_sha256):
    package = Path(package).resolve(); capture = Path(capture).resolve(); output = Path(output).resolve()
    request = cli.load(capture / 'object-request.json')
    readonly = [package, capture.parent, Path(request['source_package']).resolve(),
        Path(request['source_capture']).resolve(), Path(request['cache_entry']).resolve().parent]
    if any(output == root or root in output.parents for root in readonly) or output in capture.parents:
        raise ValueError('Recovery output must be outside original package and capture')
    if (not isinstance(expected_object_sha256, str) or len(expected_object_sha256) != 64
        or any(char not in '0123456789abcdef' for char in expected_object_sha256)):
        raise ValueError('Expected externally recorded object SHA256 required')
    output.mkdir(parents=True, exist_ok=False)
    try:
        manifest = verify_original(cli, package, capture)
        before = snapshot(cli, package, capture)
        # Alternate records are an explicit new snapshot, never a historical
        # artifacts.json backfilled into the interrupted capture.
        result = cli.audit_partition_object_capture(manifest, capture,
            module_object=True, artifact_records=before['proof'])
        if result.get('object_verified') is not True or result.get('containment_verified') is not True:
            raise ValueError('Saved module object audit failed: ' + str(result.get('error')))
        if snapshot(cli, package, capture) != before:
            raise ValueError('Original capture changed during recovery audit')
        artifact = cli.load(capture / 'object.json')['receipt']['artifact']
        if artifact['sha256'] != expected_object_sha256:
            raise ValueError('Object differs from externally recorded original SHA256')
        receipt = dict(schema=1, mode='recover-object-only', source_package=str(package),
            source_capture=str(capture), source_package_id=manifest['package_id'],
            original_snapshot=before, originally_missing=list(MISSING), original_run_status='processing',
            original_outer_timed_out=True, original_stage_verified=False, object=artifact,
            expected_object_sha256=expected_object_sha256,
            object_verified=True, containment_verified=True, preservation_verified=result['preservation_verified'],
            calculation_verified=False, link_verified=False, kernel_calls=0, gpu_calls=0,
            nvrtc_compile_calls=0, driver_load_calls=0, native_tool_calls=0,
            original_capture_modified=False, passed=result['preservation_verified'] is True)
        cli.write(output / 'result.json', receipt)
        return receipt
    except BaseException as error:
        cli.write(output / 'failure.json', dict(error=type(error).__name__ + ': ' + str(error),
            native_tool_calls=0, gpu_calls=0, original_capture_modified=False))
        raise
