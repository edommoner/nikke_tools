"""Audit a completed CUDA dispatch left under a terminal outer timeout.

The original capture is never completed or repaired. Its own immutable CLI
performs the ordinary fresh native comparison under an alternate, explicit
snapshot inventory. No saved CPU values or successful stage are manufactured.
"""
from portable_product_programs import configuration as product_configuration
from pathlib import Path
from portable_object_recovery import MISSING, verify_terminal_timeout


def verify_payload(cli, package):
    """Byte bootstrap only; semantic projection belongs to the saved CLI."""
    manifest = cli.load(package / 'gpu-package.json')
    if manifest.get('schema') != cli.SCHEMA or manifest.get('package_id') != cli.package_id(manifest):
        raise ValueError('Invalid original package identity')
    if sum(row['path'] == 'scripts/nikke_gpu.py' for row in manifest['files']) != 1:
        raise ValueError('Original controller must be in the verified payload')
    cli.check_records(package, manifest['files'])
    return manifest


def snapshot(cli, package, capture):
    result = {}
    for label, folder in (('outer', capture.parent), ('proof', capture)):
        names = []
        for path in folder.iterdir():
            if path.is_symlink():
                raise ValueError('Recovery rejects capture symlinks')
            if path.is_file():
                names.append(path.name)
        result[label] = cli.file_records(folder, sorted(names))
    result['package'] = cli.file_records(package, ['gpu-package.json',
        'gpu-claimed-cuda.json', 'packet-stage-claimed-gpu-linked-cuda.json'])
    return result


def verify_original(cli, package, capture):
    manifest = cli.verify_package(package)
    run = cli.load(capture / 'run.json')
    if (run.get('package_id') != manifest['package_id'] or run.get('mode') != 'gpu'
        or run.get('backend') != 'cuda' or run.get('status') != 'preflight'
        or cli.is_development(manifest) or cli.compiler_only(manifest)):
        raise ValueError('Recovery requires an incomplete sealed CUDA battle')
    if any((capture / name).exists() for name in (*MISSING, 'comparison.json')):
        raise ValueError('Recovery does not replace existing results or inventories')
    plan = cli.load(capture.parent / 'recipe.json')
    packet = cli.module(package / 'scripts/run-gpu-packet.py')
    expected = packet.recipe(manifest['package_id'], 'gpu-linked', 'cuda', capture.parent,
        plan['original_workspace'], plan['timeout_seconds'], plan['object_request'])
    if plan != expected or Path(plan['proof_capture']).resolve() != capture:
        raise ValueError('Recovery packet recipe mismatch')
    verify_terminal_timeout(cli, capture)
    for name, target in (('gpu-claimed-cuda.json', capture),
                         ('packet-stage-claimed-gpu-linked-cuda.json', capture.parent)):
        claim = cli.load(package / name)
        if claim.get('package_id') != manifest['package_id'] or Path(claim['capture']).resolve() != target:
            raise ValueError('Recovery consumed claim mismatch')
    request = cli.load(capture / 'linked-artifact-request.json')
    if request != dict(package=plan['object_request']['linked_package'],
                       capture=plan['object_request']['linked_capture']):
        raise ValueError('Recovery linked request mismatch')
    from portable_cpu_tests import complete
    tests = cli.load(capture / 'cpu-tests.json')
    if not complete(tests, product_configuration(cli.SUITES,manifest)['tests']):
        raise ValueError('Recovery original CPU tests incomplete')
    if cli.load(capture / 'cpu.json').get('passed') is not True:
        raise ValueError('Recovery original native preflight incomplete')
    return manifest


def recover(cli, package, capture, output, expected_output_sha256):
    package = Path(package).resolve(); capture = Path(capture).resolve(); output = Path(output).resolve()
    request = cli.load(capture / 'linked-artifact-request.json')
    plan = cli.load(capture.parent / 'recipe.json')
    readonly = [cli.ROOT.resolve(), package, capture.parent,
        Path(request['package']).resolve(), Path(request['capture']).resolve().parent,
        Path(plan['original_workspace']).resolve()]
    if any(output == root or root in output.parents or output in root.parents for root in readonly):
        raise ValueError('Recovery output must be outside original evidence')
    if (not isinstance(expected_output_sha256, str) or len(expected_output_sha256) != 64
        or any(c not in '0123456789abcdef' for c in expected_output_sha256)):
        raise ValueError('Externally recorded output SHA256 required')
    output.mkdir(parents=True, exist_ok=False)
    try:
        # Load the verified original controller; new recovery code does not
        # substitute its own suite, comparator, numeric policy or normalizer.
        source_manifest = verify_payload(cli, package)
        controller_manifest = cli.verify_package(cli.ROOT)
        current = {row['path']: row['sha256'] for row in controller_manifest['files']}
        for row in source_manifest['files']:
            name = row['path']
            critical = name.startswith(('app/', 'gpu/', 'research/upstream/')) or name.startswith('research/') and name.endswith('.py')
            if critical and name not in ('app/portable_object_recovery.py', 'app/portable_readback_recovery.py'):
                if current.get(name) != row['sha256']:
                    raise ValueError('Recovery reference/transport dependency changed: ' + name)
        original = cli.module(package / 'scripts/nikke_gpu.py')
        manifest = verify_original(original, package, capture)
        before = snapshot(cli, package, capture)
        raw = next(row for row in before['proof'] if row['path'] == 'readback.bin')
        if raw['sha256'] != expected_output_sha256 or raw['sha256'] != manifest['golden']['output_sha256']:
            raise ValueError('Readback differs from external SHA256 or sealed golden')
        cli.check_records(capture, before['proof'])
        with cli.forbid_gpu(), original.forbid_gpu():
            # This is the normal audit's fresh comparison and every transport,
            # source, compiler, Job and environment gate. Only its historical
            # inventory loader is replaced by the explicit snapshot above.
            result = original.audit_capture(capture, verify_artifacts=False)
        original.verify_package(package)
        if snapshot(cli, package, capture) != before:
            raise ValueError('Original evidence changed during recovery audit')
        receipt = dict(schema=1, mode='recover-readback-only', source_package=str(package),
            source_capture=str(capture), source_package_id=manifest['package_id'],
            original_snapshot=before, originally_missing=[*MISSING, 'comparison.json'],
            original_run_status='preflight', original_outer_timed_out=True,
            original_stage_verified=False, original_capture_modified=False,
            expected_output_sha256=expected_output_sha256, output=raw, audit=result,
            calculation_verified=result['calculation_verified'],
            containment_verified=result['containment_verified'],
            preservation_verified=result['preservation_verified'], passed=result['passed'],
            gpu_calls=0, driver_load_calls=0, native_tool_calls=0,
            native_comparison='fresh original comparator; no parent-oracle reuse')
        cli.write(output / 'result.json', receipt)
        return receipt
    except BaseException as error:
        cli.write(output / 'failure.json', dict(error=type(error).__name__ + ': ' + str(error),
            gpu_calls=0, native_tool_calls=0, original_capture_modified=False))
        raise
