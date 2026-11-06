"""Reusable decoded-payload parity gate; reference payloads are disposable caches."""
from __future__ import annotations

import ast
import concurrent.futures
import copy
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path('research/upstream/nikke-calc-master')
RESERVE = 20 * 1024**3
SCHEMA = 1


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def comparable_payload_digest(payload):
    """Compare CPU results across code versions, excluding only git provenance."""
    return digest({key: value for key, value in payload.items() if key != 'evaluator'})


def read(path):
    path = Path(path)
    if path.suffix == '.gz':
        with gzip.open(path, 'rt', encoding='utf-8-sig') as stream:
            return json.load(stream)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def load_corpus(path):
    corpus = read(path)
    if 'base' in corpus:
        corpus = copy.deepcopy(corpus)
        for row in corpus['squads']:
            row['body'] = dict(corpus['base'], **row.get('overrides', {}), squad=row['members'])
            if digest(row['body']) != row['request_sha256']:
                raise ValueError('Corpus reconstruction hash mismatch: ' + str(row['id']))
    return corpus


def save_corpus(path, rows, **metadata):
    if not rows:
        raise ValueError('Empty corpus')
    base = {k: v for k, v in rows[0]['body'].items() if k != 'squad'}
    compact = []
    for row in rows:
        body = row['body']
        if set(base) - set(body):
            raise ValueError('Corpus override cannot remove base keys')
        overrides = {k: v for k, v in body.items() if k != 'squad' and (k not in base or base[k] != v)}
        compact.append(dict(id=row['id'], members=row['members'], overrides=overrides, request_sha256=digest(body)))
    value = dict(schema=2, base=base, squads=compact, **metadata)
    path = Path(path)
    if path.suffix == '.gz':
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.tmp')
        temp.write_bytes(gzip.compress(canonical(value), mtime=0))
        temp.replace(path)
    else:
        atomic_json(path, value)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(canonical(value) + b'\n')
    temporary.replace(path)


def cpu_sources(root=ROOT):
    """AST import closure, including literal dynamic layer names, at all scopes.

    Start with every calculator source and engine_worker. Exclude only worker
    entry points explicitly returning GPU compile/audit/static/event results.
    Optional CPU reference-model imports are deliberately included.
    """
    root = Path(root)
    bases = [root / 'app', root / ENGINE]
    excluded = {'detail_gpu', 'portable_roster_input', 'portable_catalog', 'portable_runtime'}
    pending = [root / 'app/engine_worker.py', *(root / ENGINE / 'calculator').rglob('*.py')]
    found = set()

    def resolve(name):
        for base in bases:
            for candidate in (base / (name.replace('.', '/') + '.py'),
                              base / name.replace('.', '/') / '__init__.py'):
                if candidate.is_file():
                    pending.append(candidate)

    while pending:
        path = pending.pop()
        if path in found:
            continue
        found.add(path)
        tree = ast.parse(path.read_bytes(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in excluded:
                        resolve(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if node.level:
                    parent = path.parent
                    for _ in range(node.level - 1):
                        parent = parent.parent
                    for base in bases:
                        if parent.is_relative_to(base):
                            module = '.'.join((*parent.relative_to(base).parts, module)).strip('.')
                            break
                if module not in excluded:
                    resolve(module)
                    for alias in node.names:
                        resolve(module + '.' + alias.name)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                # effect_spec.COMPAT_LAYERS drives import_module(module).
                if node.value.isidentifier() and node.value not in excluded:
                    resolve(node.value)
    return sorted(p.relative_to(root).as_posix() for p in found)


def code_identity(root=ROOT):
    root = Path(root)
    files = {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
             for p in cpu_sources(root)}
    return digest(files), files


class DataIdentity:
    """Explicit safe slices; unknown/new tables conservatively remain global."""
    def __init__(self, root=ROOT):
        root = Path(root)
        self.tables = {}
        for base in (root / 'data', root / ENGINE / 'data'):
            for path in sorted(base.rglob('*.json')):
                self.tables[path.relative_to(root).as_posix()] = read(path)
        global_tables = {}
        for path, value in self.tables.items():
            name = Path(path).name
            if path.startswith(str(ENGINE)) and name in ('parsed_nikke.json', 'parsed_skills.json', 'char_defaults.json'):
                # Non-character metadata/rules are global, including future keys.
                global_tables[path] = {k: v for k, v in value.items() if k.startswith('_')}
            elif path.startswith(str(ENGINE)) and name in ('weapon_delays.json', 'burst_gauge.json'):
                global_tables[path] = {k: v for k, v in value.items() if k != '_exceptions'}
            elif path == 'data/engine-effect-overrides.json':
                global_tables[path] = {k: v for k, v in value.items() if k != 'corrections'}
            elif path == 'data/engine-revisions.json':
                # Installation verification manifest, not calculator input. Its
                # executable/data contents are independently covered here.
                continue
            else:
                global_tables[path] = value
        # buff_manager derives modal weapon ranges from the ENTIRE roster.
        # Hash the actual derived table, so harmless roster additions stay hits.
        counts = {}
        for entry in self.tables.get(str(ENGINE / 'data/parsed_nikke.json'), {}).values():
            if isinstance(entry, dict) and entry.get('weapon_type') and entry.get('optimal_range'):
                ranges = counts.setdefault(entry['weapon_type'], {})
                key = tuple(entry['optimal_range'])
                ranges[key] = ranges.get(key, 0) + 1
        global_tables['derived:type_optimal_ranges'] = {
            weapon: max(ranges, key=lambda k: (ranges[k], k)) for weapon, ranges in counts.items()}
        self.global_identity = digest(global_tables)

    def member_identity(self, members):
        slices = {}
        for path, value in self.tables.items():
            name = Path(path).name
            if path.startswith(str(ENGINE)) and name in ('parsed_nikke.json', 'parsed_skills.json', 'char_defaults.json'):
                slices[path] = {n: value.get(n) for n in members}
            elif path.startswith(str(ENGINE)) and name in ('weapon_delays.json', 'burst_gauge.json'):
                slices[path] = {n: value.get('_exceptions', {}).get(n) for n in members}
            elif path == 'data/engine-effect-overrides.json':
                slices[path] = [v for v in value['corrections'] if v['character'] in members]
        return digest(slices)

    def identities(self, body, code):
        member = self.member_identity(body['squad'])
        data = digest(dict(member=member, global_data=self.global_identity))
        identity = dict(schema=SCHEMA, request_sha256=digest(body), code_identity=code,
                        data_identity=data, member_data_identity=member,
                        global_data_identity=self.global_identity)
        return dict(identity, cache_key=digest(identity))


def cache_path(cache, key):
    return Path(cache) / key[:2] / (key + '.json.gz')


def load_cache(cache, identity):
    path = cache_path(cache, identity['cache_key'])
    if not path.exists():
        return None
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        entry = json.load(stream)
    if entry['identity'] != identity or digest(entry['payload']) != entry['payload_sha256']:
        raise ValueError('Corrupt CPU cache entry: ' + str(path))
    return entry['payload']


def save_cache(cache, identity, payload, reused_from=None):
    path = cache_path(cache, identity['cache_key'])
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(identity=identity, payload=payload, payload_sha256=digest(payload))
    if reused_from:
        entry['reused_from'] = reused_from
    raw = canonical(entry)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('wb') as stream:
        stream.write(gzip.compress(raw, mtime=0))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    return path.stat().st_size


def source_changes(old, new):
    """Pure AST comparison, with ranges in the original source coordinate space."""
    if old.keys() != new.keys():
        return dict(all_invalid=True, reasons=[dict(file=p, function='<closure>') for p in sorted(old.keys() ^ new.keys())], changed=[])
    changed = []
    def split(source):
        tree = ast.parse(source)
        bodies = {}
        def strip(node, name):
            # Duplicate definitions cannot safely be matched by qualified name.
            if name in bodies:
                raise ValueError('Duplicate definition: ' + name)
            bodies[name] = (ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False),
                            node.body[0].lineno, node.body[-1].end_lineno)
            node.body = [ast.Pass()]
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                strip(node, node.name)
            elif isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        strip(method, node.name + '.' + method.name)
        return ast.dump(tree, include_attributes=False), bodies
    for path in sorted(old):
        if old[path] == new[path]:
            continue
        try:
            # Equal ASTs are harmless even when duplicate qualified names
            # (e.g. property accessors) make body-by-name matching ambiguous.
            if ast.dump(ast.parse(old[path]), include_attributes=False) == ast.dump(
                    ast.parse(new[path]), include_attributes=False):
                continue
            skeleton, bodies = split(old[path])
            new_skeleton, new_bodies = split(new[path])
        except (SyntaxError, ValueError):
            return dict(all_invalid=True, reasons=[dict(file=path, function='<unparseable-or-ambiguous>')], changed=[])
        if skeleton != new_skeleton:
            return dict(all_invalid=True, reasons=[dict(file=path, function='<module>')], changed=[])
        for name, (body, first, last) in bodies.items():
            if body != new_bodies[name][0]:
                changed.append(dict(file=path, function=name, first=first, last=last))
    return dict(all_invalid=False, reasons=[], changed=changed)


def coverage_valid(analysis, lines):
    reasons = list(analysis['reasons'])
    if not analysis['all_invalid']:
        reasons.extend(c for c in analysis['changed'] if any(c['first'] <= n <= c['last'] for n in lines.get(c['file'], [])))
    return not reasons, reasons


def atomic_gzip(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('wb') as stream:
        stream.write(gzip.compress(raw, mtime=0)); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def coverage_path(cache, key):
    return cache_path(cache, key).with_name(key + '.cov.json.gz')


def store_sources(cache, sources, root=ROOT):
    for path, sha in sources.items():
        raw = (Path(root) / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError('Source changed during run: ' + path)
        target = Path(cache) / 'sources' / (sha + '.gz')
        if not target.exists():
            atomic_gzip(target, raw)


def stored_sources(cache, sources):
    result = {}
    for path, sha in sources.items():
        raw = gzip.decompress((Path(cache) / 'sources' / (sha + '.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError('Corrupt stored source: ' + path)
        result[path] = raw.decode('utf-8-sig')
    return result


class LineRecorder:
    """Global presence events begin before importing any identity module."""
    def __init__(self, sources, root=ROOT):
        self.paths = {str((Path(root) / p).resolve()): p for p in sources}
        self.lines = {}
        self.tool = 5

    def __enter__(self):
        imported = sorted({self.paths[str(Path(m.__file__).resolve())] for m in tuple(sys.modules.values())
                           if getattr(m, '__file__', None) and str(Path(m.__file__).resolve()) in self.paths})
        if imported:
            raise RuntimeError('Code identity modules already imported: ' + ', '.join(imported))
        sys.monitoring.use_tool_id(self.tool, 'parity-reference-lines')
        filenames = {}
        def line(code, number):
            filename = code.co_filename
            if filename not in filenames:
                filenames[filename] = self.paths.get(str(Path(filename).resolve()))
            path = filenames[filename]
            if path is not None:
                self.lines.setdefault(path, set()).add(number)
            return sys.monitoring.DISABLE
        sys.monitoring.register_callback(self.tool, sys.monitoring.events.LINE, line)
        sys.monitoring.set_events(self.tool, sys.monitoring.events.LINE)
        return self

    def __exit__(self, *exc):
        sys.monitoring.set_events(self.tool, 0)
        sys.monitoring.register_callback(self.tool, sys.monitoring.events.LINE, None)
        sys.monitoring.free_tool_id(self.tool)


def original_entry(cache, entry):
    seen = set()
    expected = entry['identity']
    payload_sha = entry['payload_sha256']
    while entry.get('reused_from'):
        key = entry['reused_from']
        if key in seen:
            raise ValueError('CPU alias cycle')
        seen.add(key)
        entry = read(cache_path(cache, key))
        if (entry['identity']['cache_key'] != key or
                any(entry['identity'][field] != expected[field] for field in ('request_sha256', 'data_identity')) or
                entry['payload_sha256'] != payload_sha):
            raise ValueError('Corrupt CPU alias target: ' + key)
    if digest(entry['payload']) != entry['payload_sha256']:
        raise ValueError('Corrupt original CPU payload')
    return entry


def older_entries(cache, identity):
    entries = []
    for path in sorted(Path(cache).glob('*/*.json.gz')):
        if path.name.endswith('.cov.json.gz'):
            continue
        entry = read(path)
        old = entry['identity']
        if (old['request_sha256'] == identity['request_sha256'] and old['data_identity'] == identity['data_identity']
                and old['code_identity'] != identity['code_identity']):
            entries.append(original_entry(cache, entry))
    return list({e['identity']['cache_key']: e for e in entries}.values())


def coverage_candidate(cache, entries, sources):
    reasons = []
    current = None
    for entry in entries:
        key = entry['identity']['cache_key']
        sidecar = coverage_path(cache, key)
        if not sidecar.exists():
            continue
        cov = read(sidecar)
        if cov['cache_key'] != key or digest(cov['code_identity']) != entry['identity']['code_identity']:
            raise ValueError('Corrupt coverage identity: ' + key)
        try:
            old = stored_sources(cache, cov['code_identity'])
        except FileNotFoundError:
            continue
        if current is None:
            current = stored_sources(cache, sources)
        valid, invalid = coverage_valid(source_changes(old, current), cov['lines'])
        if valid:
            return entry, []
        reasons.extend(invalid)
    return None, reasons


def spot_check_selected(request, fraction, seed):
    return int(digest([seed, request]), 16) / 2**256 < fraction


def reference_payload(body, identity, cache, sources, full=False, inherited_identity=None,
                      spot_fraction=0.02, seed=20261106):
    cpu = None if full else load_cache(cache, identity)
    result = dict(reference_identity=identity, reference_status='current-reference', cache_hit=cpu is not None,
                  cpu_evaluations=0, spot_checked=False, spot_check_failure=False, invalidating=[])
    if cpu is not None:
        return cpu, result
    entries = older_entries(cache, identity)
    candidate, reasons = coverage_candidate(cache, entries, sources) if not full else (None, [])
    result['invalidating'] = reasons
    if candidate:
        cpu = candidate['payload']
        result['reference_status'] = 'coverage-reused'
        if spot_check_selected(identity['request_sha256'], spot_fraction, seed):
            checked = cpu_job(body, sources, cache, identity, save=False)
            equal = comparable_payload_digest(checked) == comparable_payload_digest(cpu)
            result.update(cpu_evaluations=1, spot_checked=True,
                          spot_check_failure=not equal,
                          previous_code_payload_equal=equal,
                          previous_code_cache_key=candidate['identity']['cache_key'])
        if not result['spot_check_failure']:
            save_cache(cache, identity, cpu, reused_from=candidate['identity']['cache_key'])
        return cpu, result
    if inherited_identity and not full and not reasons:
        cpu = load_cache(cache, inherited_identity)
        if cpu is not None:
            result.update(reference_identity=inherited_identity, reference_status='inherited-from-previous-reference', cache_hit=True)
            return cpu, result
    cpu = cpu_job(body, sources, cache, identity)
    result['cpu_evaluations'] = 1
    if entries:
        result['previous_code_payload_equal'] = comparable_payload_digest(cpu) == comparable_payload_digest(entries[0]['payload'])
        result['previous_code_cache_key'] = entries[0]['identity']['cache_key']
    return cpu, result


def storage_check(required=0, path=ROOT):
    free = shutil.disk_usage(path).free
    if free < RESERVE + required:
        raise RuntimeError(f'Storage reserve: {free} free; need {required} additional + {RESERVE} reserve')
    return free


def build_corpus(args):
    if getattr(args, 'cover', None) or getattr(args, 'extend_for_character', None):
        from parity_corpus import build
        return build(args)
    source = read(ROOT / 'research/team-search/s1-inputs.json')
    base = read(args.benchmark or source['benchmark'])[0]
    base.update(source['settings'])
    rows = [json.loads(line) for line in (ROOT / 'research/team-search/s1-results.jsonl').read_text().splitlines()]
    squads = [dict(id=r['id'], members=r['members'], body=dict(base, squad=r['members'])) for r in rows]
    if getattr(args, 'corpus', None):
        squads = load_corpus(args.corpus)['squads']
        base = {k: copy.deepcopy(v) for k, v in squads[0]['body'].items() if k != 'squad'}
    if args.include_character:
        name = args.include_character
        if name not in base['profile']['chars']:
            import engine_worker
            if name not in engine_worker.META:
                raise ValueError('Unknown canonical character: ' + name)
            base['profile']['chars'][name] = {
                k: copy.deepcopy(v) for k, v in engine_worker.spec.DEFAULT_CHAR.items()
                if k in engine_worker.spec.GROWTH_KEYS}
        rng = random.Random(args.seed)
        available = sorted(set(base['profile']['chars']) - {name})
        from parity_corpus import covered
        import engine_worker
        scored = engine_worker.candidate_scores(dict(evaluation=base))
        chars = {c['name']: c for c in scored['characters']}
        available = [n for n in available if n in chars]
        seen = {digest(r['body']) for r in squads}
        added = 0
        while added < args.count:
            members = [name, *rng.sample(available, 4)]
            rng.shuffle(members)
            if not covered(members, chars):
                continue
            body = dict(base, squad=members)
            if digest(body) in seen:
                continue
            seen.add(digest(body))
            squads.append(dict(id=max(r['id'] for r in squads) + 1, members=members, body=body))
            added += 1
    save_corpus(args.output, squads, seed=args.seed)
    print(json.dumps(dict(corpus=str(args.output), squads=len(squads))))


def native_job(row, scratch):
    if (Path(scratch).parent / 'STOP').exists():
        raise InterruptedError('Stop requested; remove STOP to resume')
    import portable_detail
    if os.environ.get('NIKKE_PARITY_NATIVE_ROOT'):
        import portable_backend
        portable_backend.ROOT = Path(os.environ['NIKKE_PARITY_NATIVE_ROOT'])
    from portable_native import HOST_THREADS
    HOST_THREADS.set(1)
    # Captures are disposable transport scratch; decoded results are retained.
    with tempfile.TemporaryDirectory(prefix='native-', dir=scratch) as tmp:
        os.environ['NIKKE_DETAIL_CAPTURE_ROOT'] = tmp
        result = portable_detail.evaluate_many([row['body']], verification='deferred')[0]
        if result.get('error'):
            return dict(error=result['error'])
        return dict(payload=result['result'])


def cpu_job(body, sources=None, cache=None, identity=None, save=True):
    if sources is None:
        raise ValueError('CPU reference requires code identity sources')
    with LineRecorder(sources) as recorder:
        import engine_worker
        payload = engine_worker.evaluate(body)
    if save:
        save_cache(cache, identity, payload)
    # Spot checks also retain the fresh trace. Aliases still resolve to their
    # original trace for future cross-version analysis.
    atomic_gzip(coverage_path(cache, identity['cache_key']), canonical(dict(
        cache_key=identity['cache_key'], code_identity=sources,
        lines={p: sorted(lines) for p, lines in recorder.lines.items()})))
    return payload


def plan_storage(rows, workers):
    import portable_detail
    budgets = []
    for row in rows:
        try:
            prepared, _ = portable_detail.prepare(row['body'])
            _, iw, ow, *_ = portable_detail.compile_product(prepared)
            budgets.append((3 * iw + 2 * ow) * 4)
        except Exception:
            # Deferred admission failures write no battle buffers.
            continue
    return sum(sorted(budgets, reverse=True)[:workers]) + 1024**3


def run(args):
    # The supported native platforms provide advisory POSIX locks. A killed
    # coordinator releases the lock automatically; stale files do not block resume.
    import fcntl
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / '.run.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('Another process is writing this run directory') from error
        return _run(args)


def _run(args):
    start = time.perf_counter()
    storage_check(1024**3)
    from portable_native import availability, clang_compiler
    available = availability(ROOT)
    if not available['available']:
        raise RuntimeError(available['reason'] + ' Set NIKKE_SLANG_ROOT to the installed compiler directory.')
    if not 0 <= args.sample_fraction <= 1:
        raise ValueError('sample-fraction must be 0..1')
    spot_fraction = getattr(args, 'coverage_spot_check', 0.02)
    if not 0 <= spot_fraction <= 1:
        raise ValueError('coverage-spot-check must be 0..1')
    corpus = load_corpus(args.corpus)
    rows = corpus['squads']
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate corpus IDs')
    for row in rows:
        if any(k.startswith('_') or k == 'verification' for k in row['body']):
            raise ValueError('Corpus bodies cannot contain internal evaluation controls')
        if row['members'] != row['body']['squad'] or row['body'].get('compute_backend') != 'native_detail':
            raise ValueError('Corpus must contain complete native_detail bodies with matching members')
    identity_root = Path(getattr(args, 'coverage_test_code_root', None) or ROOT).resolve()
    code, sources = code_identity(identity_root)
    if identity_root != ROOT and Path(args.cache).resolve() == (ROOT / 'research/parity/cpu-cache').resolve():
        raise ValueError('Coverage test override requires a separate disposable cache')
    data = DataIdentity()
    identities = {r['id']: data.identities(r['body'], code) for r in rows}
    if getattr(args, 'require_cache', False):
        absent = [r['id'] for r in rows if load_cache(args.cache, identities[r['id']]) is None]
        if absent:
            raise ValueError('Required CPU cache missing for squads: ' + str(absent))
    native_root = (getattr(args, 'native_root', None) or ROOT).resolve()
    if native_root != ROOT:
        os.environ['NIKKE_PARITY_NATIVE_ROOT'] = str(native_root)
    else:
        os.environ.pop('NIKKE_PARITY_NATIVE_ROOT', None)
    previous = read(args.previous) if args.previous else None
    prev = {r['identity']['request_sha256']: r for r in previous['squads']} if previous else {}
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    store_sources(cache, sources, identity_root)
    scratch = output / 'scratch'
    scratch.mkdir(exist_ok=True)
    # Resume binds decoded native results to their executing source, not raw counters.
    native_sources = subprocess.check_output(['git', 'ls-files', 'app', 'gpu', 'scripts/native-product-host.cpp'], cwd=ROOT, text=True).splitlines()
    from portable_slang_generation import slang_compiler
    compiler = slang_compiler(ROOT)
    native_identity = digest(dict(sources={p: hashlib.sha256(((native_root if p.startswith('gpu/') or p == 'scripts/native-product-host.cpp' else ROOT) / p).read_bytes()).hexdigest()
                              for p in native_sources if (ROOT / p).is_file()},
                              gate=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                              slangc=hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
                              clang=subprocess.check_output([clang_compiler(), '--version'], text=True)))
    config = dict(schema=SCHEMA, corpus=digest(corpus), code=code, global_data=data.global_identity,
                  identities=digest(identities), native=native_identity, full=args.full,
                  sample_fraction=args.sample_fraction, coverage_spot_check=spot_fraction, seed=args.seed,
                  coverage_test_code_root=str(identity_root) if identity_root != ROOT else None,
                  previous=digest(previous) if previous else None)
    manifest = output / 'manifest.json'
    if manifest.exists() and read(manifest)['config'] != config:
        raise ValueError('Run inputs changed; use a new output directory to retain prior evidence')
    if not manifest.exists():
        atomic_json(manifest, dict(config=config, cpu_sources=sources, sessions=[]))
    record = read(manifest)
    for session in record['sessions']:
        if session.get('state') == 'running':
            session['state'] = 'interrupted'
    session_index = len(record['sessions'])
    record['sessions'].append(dict(started_at=time.time(), seconds=0, completed=0, state='running'))
    atomic_json(manifest, record)
    journal = output / 'results.jsonl'
    done = {}
    if journal.exists():
        # Recover a torn final append; completed lines remain authoritative.
        with journal.open('rb+') as stream:
            while True:
                pos = stream.tell()
                line = stream.readline()
                if not line:
                    break
                if not line.endswith(b'\n'):
                    stream.truncate(pos)
                    break
                item = json.loads(line)
                if item['id'] in done:
                    raise ValueError('Duplicate result ID')
                done[item['id']] = item
    pending = [r for r in rows if r['id'] not in done]
    required = plan_storage(pending, args.workers)
    minfree = storage_check(required)
    print(json.dumps(dict(pending=len(pending), peak_additional_bytes=required, free=minfree)), flush=True)
    # Exact-count deterministic sample, chosen only among stale, unchanged-member references.
    eligible = []
    for row in rows:
        ident = identities[row['id']]
        old = prev.get(ident['request_sha256'])
        if old and old['identity']['member_data_identity'] == ident['member_data_identity'] and (
                old['identity']['code_identity'] != code or old['identity']['global_data_identity'] != data.global_identity):
            eligible.append(ident['request_sha256'])
    sample = set(random.Random(args.seed).sample(sorted(set(eligible)), math.ceil(len(set(eligible)) * args.sample_fraction)))
    native_dir = output / 'native'
    native_dir.mkdir(exist_ok=True)
    # Continuously refill ten slots; a slow CPU squad never stalls a batch.
    # Each task gets a fresh interpreter for the adapter's monkeypatch contract.
    with journal.open('ab') as stream, concurrent.futures.ProcessPoolExecutor(
            max_workers=args.workers, max_tasks_per_child=1) as pool:
        iterator = iter(pending)
        futures = {}

        def submit(row):
            ident = identities[row['id']]
            old = prev.get(ident['request_sha256'])
            inherit = (old.get('reference_identity', old['identity']) if old and
                       ident['request_sha256'] in eligible and
                       ident['request_sha256'] not in sample and not args.full else None)
            futures[pool.submit(row_job, row, ident, old, inherit, args.full,
                                cache, native_dir, scratch, sources, spot_fraction, args.seed)] = row['id']

        for _ in range(min(args.workers, len(pending))):
            submit(next(iterator))
        while futures:
            finished, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in finished:
                futures.pop(future)
                result = future.result()
                stream.write(canonical(result) + b'\n')
                stream.flush()
                os.fsync(stream.fileno())
                done[result['id']] = result
                record['sessions'][session_index].update(seconds=time.perf_counter()-start, completed=len(done)-(len(rows)-len(pending)))
                atomic_json(manifest, record)
                minfree = min(minfree, storage_check(required))
                if len(done) % 10 == 0 or len(done) == len(rows):
                    print(json.dumps(dict(completed=len(done), total=len(rows), seconds=round(time.perf_counter()-start, 2),
                                          cpu_evaluations=sum(r['cpu_evaluations'] for r in done.values()))), flush=True)
                row = next(iterator, None)
                if row is not None:
                    submit(row)
    ordered = [done[r['id']] for r in rows]
    counts = {s: sum(r['status'] == s for r in ordered) for s in ('matched', 'mismatched', 'cpu-fallback', 'unsupported')}
    chars = {}
    for row in ordered:
        for name in row['members']:
            table = chars.setdefault(name, dict(squads=0, mismatched=0, inherited=0))
            table['squads'] += 1
            table['mismatched'] += row['status'] == 'mismatched'
            table['inherited'] += row['reference_status'] == 'inherited-from-previous-reference'
    sizes = [p.stat().st_size for p in cache.glob('*/*.json.gz') if not p.name.endswith('.cov.json.gz')]
    elapsed = time.perf_counter() - start
    record['sessions'][session_index].update(seconds=elapsed, completed=len(pending), min_free=minfree, state='complete')
    atomic_json(manifest, record)
    regressions = [r['id'] for r in ordered if r['regression']]
    summary = dict(schema=SCHEMA, counts=counts, total=len(ordered), cache_hits=sum(r['cache_hit'] for r in ordered),
                   cache_misses=sum(not r['cache_hit'] for r in ordered), cpu_evaluations=sum(r['cpu_evaluations'] for r in ordered),
                   inherited=sum(r['reference_status'] == 'inherited-from-previous-reference' for r in ordered),
                   current_reference_counts={s: sum(r['status'] == s and r['reference_status'] in ('current-reference', 'coverage-reused') for r in ordered) for s in counts},
                   inherited_reference_counts={s: sum(r['status'] == s and r['reference_status'] == 'inherited-from-previous-reference' for r in ordered) for s in counts},
                   regressions=regressions, new_matches=[r['id'] for r in ordered if r['new_match']],
                   seconds=elapsed, cumulative_seconds=sum(s['seconds'] for s in record['sessions']),
                   cache_size=dict(entries=len(sizes), total_bytes=sum(sizes), min_bytes=min(sizes, default=0), max_bytes=max(sizes, default=0)),
                   min_free=minfree, peak_additional_bytes=required, per_character=chars, squads=ordered)
    summary.update(fresh=sum(r['cpu_evaluations'] and not r['spot_checked'] for r in ordered),
                   coverage_reused=sum(r['reference_status'] == 'coverage-reused' for r in ordered),
                   spot_checked=sum(r['spot_checked'] for r in ordered),
                   spot_check_failures=sum(r['spot_check_failure'] for r in ordered),
                   previous_code_payload_equal={str(equal): sum(r.get('previous_code_payload_equal') is equal for r in ordered)
                                                for equal in (True, False)})
    atomic_json(output / 'summary.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ('squads', 'per_character')}, ensure_ascii=False), flush=True)
    # Without a previous run every mismatch is a new finding and fails the gate.
    return run_failed(summary)


def row_job(row, identity, previous, inherited_identity, full, cache, native_dir, scratch,
            sources, spot_fraction=0.02, seed=20261106):
    # Reference must precede native preparation, which imports identity modules.
    cpu, reference_result = reference_payload(row['body'], identity, cache, sources, full,
                                               inherited_identity, spot_fraction, seed)
    path = native_dir / (str(row['id']) + '.json.gz')
    if path.exists():
        native = read(path)
    else:
        native = native_job(row, scratch)
        if native.get('error'):
            raise RuntimeError(f"Native row {row['id']}: {native['error']}")
        atomic_gzip(path, canonical(native))
    reference = reference_result['reference_identity']
    result = dict(id=row['id'], members=row['members'], identity=identity, **reference_result,
                  cache_bytes=cache_path(cache, reference['cache_key']).stat().st_size
                  if cache_path(cache, reference['cache_key']).exists() else 0)
    finish_result(result, native['payload'], cpu, previous)
    return result


def finish_result(result, native, cpu, previous):
    from portable_detail import payload_differences
    fallback = native.get('cpu_fallback_pending')
    backend = native.get('compute', {}).get('backend')
    if fallback:
        status, differences = 'unsupported', []
        result['unsupported'] = fallback
    elif backend != 'native_detail':
        status, differences = 'cpu-fallback', []
    else:
        differences = sorted(payload_differences(native, cpu))
        status = 'mismatched' if differences else 'matched'
    result.update(status=status, differing_fields=differences,
                  regression=(status != 'matched' and (previous is None or previous['status'] == 'matched')),
                  new_match=(status == 'matched' and previous is not None and previous['status'] != 'matched'))


def run_failed(summary):
    return int(summary['spot_check_failures'] > 0 or bool(summary['regressions'])
               or summary['counts']['unsupported'] > 0 or summary['counts']['cpu-fallback'] > 0)
