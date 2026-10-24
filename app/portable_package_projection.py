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
SUPPORTED_SUITES = ('destructible-skill-retention', 'destructible-skill-misato-retention',
                    'destructible-aoe-burst-rosters','destructible-body-lifesteal',
                    'destructible-body-lifesteal-retention')
RUNTIME_ROOTS = ('research/run-world-bounded.py', 'research/portable_phase_audit.py',
                 'research/summarize-portable-cross-gpu.py')
# These registries describe commands outside this profile, not runtime imports.
LITERAL_REGISTRIES = {'scripts/nikke_gpu.py'}
UNSUPPORTED_COMMANDS = {'package', 'reference', 'inventory', 'consumer-audit', 'audit-legacy',
                        'cases', 'compiler-certificate'}


def roots_for(config, smoke_tests):
    return sorted({*RUNTIME_ROOTS, config['script'],
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
