"""Conservative, opt-in Python payload projection; never a calculation proof.

Only research/test Python files outside the pinned reference may be omitted.
All application/controller code, GPU sources, fixtures and public data survive.
Dynamic imports are followed by module/file literals, keeping every ambiguous
match. This is a packaging aid, not a general Python dependency resolver.
"""
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import PurePosixPath

PROFILE = 'selected-suite-python-v1'
SUPPORTED_SUITES = ('coordinate-typed-live-aim', 'coordinate-typed-geometry', 'coordinate-typed', 'original-modifier-probe', 'coordinate-original-owned', 'coordinate-original-accum', 'coordinate-original-harmful-stack', 'coordinate-original-enemy-stack', 'coordinate-original-init', 'coordinate-original-shared', 'coordinate-original-decoy', 'coordinate-original-cover', 'coordinate-original-shield','coordinate-original-reload','coordinate-original-ammo','coordinate-original-stacks','coordinate-original-cleanse','coordinate-original-source', 'coordinate-original-resources', 'coordinate-original-burst-revival', 'coordinate-original-revival', 'coordinate-original-lifecycle', 'coordinate-original-periodic', 'coordinate-original', 'coordinate-healing', 'coordinate-auto-reload', 'coordinate-mode-actions', 'coordinate-burst-control', 'burst-control-policy', 'destructible-skill-retention', 'destructible-skill-misato-retention',
                    'destructible-aoe-burst-rosters','destructible-body-lifesteal',
                    'destructible-body-lifesteal-retention',
                    'destructible-body-accum','destructible-body-accum-retention',
                    'destructible-body-heal-share','destructible-body-heal-share-retention',
                    'attack-group-battle','attack-group-native-route','attack-group-long','attack-group-mixed','coordinate-math','coordinate-shape','coordinate-arcs','coordinate-arc-arena','coordinate-arc-scalar','coordinate-numeric','coordinate-geometry','coordinate-power','coordinate-sample','coordinate-sampled-battle','coordinate-sampled-parent','coordinate-sampled-skill','coordinate-sampled-burst','coordinate-sampled-vital','coordinate-sampled-delivery','coordinate-manual','coordinate-policy','coordinate-squad','coordinate-squad-mode','coordinate-landing','coordinate-landing-arena','coordinate-landing-arena-cache-only','coordinate-landing-cache-only','packet-integer','packet-ratio','coordinate-area','coordinate-pending','coordinate-full-burst','coordinate-generation','coordinate-composed','coordinate-physical','coordinate-quantity','coordinate-accum-emission','coordinate-core','coordinate-round','coordinate-cache','coordinate-matrix','coordinate-aim','coordinate-control','coordinate-group','coordinate-mixed','coordinate-scene','coordinate-world-pool','coordinate-skills','coordinate-dot','compiler-full--attack-group-mixed','compiler-full--coordinate-resident-arc','coordinate-resident-device','compiler-full--coordinate-resident-frames','resident-frames-device','coordinate-resident-frames')
RUNTIME_ROOTS = ('research/run-world-bounded.py', 'research/portable_phase_audit.py',
                 'research/summarize-portable-cross-gpu.py')
# These registries describe commands outside this profile, not runtime imports.
LITERAL_REGISTRIES = {'scripts/nikke_gpu.py'}
UNSUPPORTED_COMMANDS = {'package', 'reference', 'inventory', 'entry-inventory', 'consumer-audit', 'audit-legacy',
                        'cases', 'compiler-certificate'}


def roots_for(config, smoke_tests):
    script=config['script']
    if script is None and config.get('compiler_only') is not True:
        raise ValueError('Only a literal compiler-only suite may omit its adapter')
    if script is not None and (not isinstance(script,str) or not script):
        raise ValueError('A selected-suite adapter must be a nonempty path')
    return sorted({*RUNTIME_ROOTS, *([script] if script is not None else []),
                   *('tests/' + name for name in (*config['tests'], *smoke_tests))})


def prunable(name):
    path = PurePosixPath(name)
    return (path.suffix == '.py' and path.parts[0] in ('research', 'tests')
            and path.parts[:2] != ('research', 'upstream'))


def project(root, names, roots, *, suite_tests=None):
    """Resolve only within the original whitelist; never add an untracked file."""
    candidates = set(names)
    missing = set(roots) - candidates
    if missing:
        raise ValueError('Compact package root absent from whitelist: ' + ', '.join(sorted(missing)))
    modules = defaultdict(set)
    filenames = defaultdict(set)
    for name in candidates:
        path = PurePosixPath(name)
        if path.suffix != '.py':
            continue
        filenames[path.name].add(name)
        modules[path.stem].add(name)
        modules[str(path.with_suffix('')).replace('/', '.')].add(name)
        if path.name == '__init__.py':
            modules[str(path.parent).replace('/', '.')].add(name)
            modules[path.parent.name].add(name)
    retained = {name for name in candidates if not prunable(name)} | set(roots)
    # Exact source audits read named Python files from their ledgers too.
    # Follow only explicit path keys already in the public whitelist, never
    # historical source text or arbitrary filesystem paths from JSON values.
    for name in sorted(candidates):
        path=PurePosixPath(name)
        if path.parts[:2]!=('tests','fixtures') or not path.name.endswith('source-delta.json'):continue
        ledger=json.loads((root/name).read_text(encoding='utf-8'))
        for section in ('files','sources','added_sources'):
            rows=ledger.get(section,{})
            if isinstance(rows,dict):retained.update(dependency for dependency in rows if dependency in candidates and prunable(dependency))
        transport=ledger.get('transport',{})
        if isinstance(transport,dict):
            dependency=transport.get('path')
            if dependency in candidates and prunable(dependency):retained.add(dependency)
    pending = sorted(retained)
    visited = set()
    while pending:
        name = pending.pop()
        if name in visited or not name.endswith('.py'):
            continue
        visited.add(name)
        tree = ast.parse((root / name).read_text(encoding='utf-8-sig'), filename=name)
        dependencies = set()
        for node in ast.walk(tree):
            # Controller fault tests also build synthetic packets from an
            # explicitly named registry suite. Keep that suite's test files;
            # this is a file dependency, not permission to execute the suite.
            if (name not in LITERAL_REGISTRIES and isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute)
                    and node.value.attr == 'SUITES' and isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, str)):
                for test in (suite_tests or {}).get(node.slice.value, ()):
                    dependency='tests/' + test
                    if dependency not in candidates:
                        raise ValueError('Controller suite test absent from whitelist: ' + dependency)
                    dependencies.add(dependency)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.update(modules[alias.name])
            elif isinstance(node, ast.ImportFrom):
                prefix = node.module or ''
                dependencies.update(modules[prefix])
                for alias in node.names:
                    dependencies.update(modules[prefix + '.' + alias.name])
                    dependencies.update(modules[alias.name])
            elif (name not in LITERAL_REGISTRIES and isinstance(node, ast.Constant)
                  and isinstance(node.value, str)):
                value = node.value.replace('\\', '/')
                dependencies.update(modules[value])
                if value.endswith('.py'):
                    dependencies.update(filenames[PurePosixPath(value).name])
        for dependency in sorted(dependencies - retained):
            retained.add(dependency)
            pending.append(dependency)
    omitted = sorted(candidates - retained)
    inventory = json.dumps(sorted(candidates), separators=(',', ':')).encode()
    metadata = dict(profile=PROFILE, roots=sorted(set(roots)),
                    original_files=len(candidates), retained_files=len(retained),
                    omitted_files=len(omitted),
                    omitted_bytes=sum((root / name).stat().st_size for name in omitted),
                    original_names_sha256=hashlib.sha256(inventory).hexdigest(),
                    omitted=omitted, calculation_verified=False, gpu_calls=0)
    return sorted(retained), metadata


def validate(metadata, files, suite, config, smoke_tests):
    names = {row['path'] for row in files}
    omitted = metadata.get('omitted', [])
    if (suite not in SUPPORTED_SUITES or metadata.get('profile') != PROFILE
            or metadata.get('roots') != roots_for(config, smoke_tests)
            or not set(metadata['roots']) <= names
            or metadata.get('retained_files') != len(names)
            or metadata.get('omitted_files') != len(omitted)
            or len(set(omitted)) != len(omitted)
            or set(omitted) & names or not all(prunable(name) for name in omitted)
            or metadata.get('original_files') != len(names) + len(omitted)
            or metadata.get('calculation_verified') is not False or metadata.get('gpu_calls') != 0):
        raise ValueError('Invalid compact package projection')
    inventory = json.dumps(sorted(names | set(omitted)), separators=(',', ':')).encode()
    if hashlib.sha256(inventory).hexdigest() != metadata.get('original_names_sha256'):
        raise ValueError('Compact package inventory mismatch')


def check_command(metadata, command):
    if metadata and command in UNSUPPORTED_COMMANDS:
        raise ValueError('Compact package supports its selected suite and saved-result tools; '
                         'use the full checkout/package for ' + command)


def validate_historical(root,manifest,cli):
    """Validate old roots with their verified owning registry, never new tests.

    The caller has already checked every payload byte. This fresh process
    runs only the original projection validator; it does not rehash the whole
    package, execute native references or load a GPU/compiler.
    """
    import os,subprocess,sys
    from pathlib import Path
    root=Path(root).resolve()
    names=['gpu-package.json','scripts/nikke_gpu.py','app/portable_package_projection.py']
    before=cli.file_records(root,names)
    records={row['path']:row for row in manifest['files']}
    if cli.load(root/'gpu-package.json')!=manifest or any(records.get(row['path'])!=row for row in before if row['path']!='gpu-package.json'):
        raise ValueError('Historical registry differs from verified payload')
    expected=next(row['sha256'] for row in before if row['path']=='gpu-package.json')
    script="""import hashlib,importlib.util,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);raw=(root/'gpu-package.json').read_bytes()
if hashlib.sha256(raw).hexdigest()!=sys.argv[2]:raise ValueError('Historical manifest changed')
s=importlib.util.spec_from_file_location('historical_projection_owner',root/'scripts/nikke_gpu.py')
owner=importlib.util.module_from_spec(s);s.loader.exec_module(owner)
m=json.loads(raw)
if m['package_id']!=owner.package_id(m):raise ValueError('Historical identity changed')
from portable_package_projection import validate
validate(m['payload_projection'],m['files'],m['suite'],owner.SUITES[m['suite']],owner.SMOKE_TESTS)
print(json.dumps(dict(package_id=m['package_id'],manifest_sha256=sys.argv[2],projection_verified=True,gpu_calls=0,native_calls=0)))
"""
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    result=subprocess.run([sys.executable,'-B','-c',script,str(root),expected],cwd=root,env=env,
        capture_output=True,text=True,check=True,timeout=30)
    proof=json.loads(result.stdout)
    if (proof!=dict(package_id=manifest['package_id'],manifest_sha256=expected,projection_verified=True,gpu_calls=0,native_calls=0)
        or cli.file_records(root,names)!=before):raise ValueError('Historical projection ownership changed')
    return proof
