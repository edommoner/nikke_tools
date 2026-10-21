"""Portable GPU proof CLI. Packages are immutable inputs; captures are append-only runs."""
import argparse
import array
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import runpy
import site
import subprocess
import sys
import time
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/p) for p in ('app', 'research', 'scripts')]
# No GPU/backend/native imports at startup: collect/audit must work without them.
SUITES = {
    'projectile': dict(script='research/verify-world-projectile-short.py',
                       golden='research/portable-world-projectile-short-expected.json',
                       source='gpu/world_projectile_entry.slang', inputs=63, native=52,
                       tests=['test_portable_projectiles.py', 'test_portable_real_binding_proof.py','test_portable_readiness.py','test_portable_compile_cache.py']),
    'readiness':dict(script='research/verify-world-readiness-short.py',
                       golden='research/portable-world-readiness-v5-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=81,native=60,
                       tests=['test_portable_readiness.py','test_portable_burst_recipients.py','test_portable_compile_cache.py','test_portable_gpu_cli.py','test_portable_compile_cli.py','test_portable_cuda_artifact.py','test_portable_phase_audit.py','test_portable_windows_cleanup.py','test_portable_windows_observer.py']),
    'recipients':dict(script='research/verify-world-recipients-short.py',
                       golden='research/portable-world-recipients-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=6,native=6,
                       tests=['test_portable_recipient_extension.py']),
    'burst-recipients':dict(script='research/verify-world-burst-recipients-short.py',
                       golden='research/portable-world-burst-recipients-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=13,native=13,
                       tests=['test_portable_burst_recipients.py']),
    'lost-hp-roster':dict(script='research/verify-world-lost-hp-rosters-short.py',
                       golden='research/portable-world-projectile-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=8,native=8,development_only=True,
                       tests=['test_portable_readiness.py','test_portable_real_binding_proof.py']),
    'reload': dict(script='research/verify-world-reload-short.py',
                   golden='research/portable-world-reload-short-expected.json',
                   source='gpu/world_reload_entry.slang', inputs=65, native=46,
                   tests=['test_portable_world_reload.py']),
}
SUITES['lost-hp-diagnostic']=dict(SUITES['lost-hp-roster'],source='gpu/world_projectile_admission_entry.slang')
SUITES['stun']=dict(script='research/verify-world-stun-short.py',golden='research/portable-world-stun-short-expected.json',
                   source='gpu/world_projectile_entry.slang',inputs=46,native=36,
                   tests=['test_portable_stun.py'])
SUITES['burst-recipients-diagnostic']=dict(SUITES['burst-recipients'],source='gpu/world_projectile_admission_entry.slang',development_only=True)
SUITES['roster-regression']=dict(script='research/verify-world-roster-regression-short.py',
    golden='research/portable-world-roster-regression-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=86,native=86,
    tests=['test_portable_roster_regression.py','test_portable_real_binding_proof.py'])
SUITES['skill-cooldown']=dict(script='research/verify-world-skill-cooldown-short.py',
    golden='research/portable-world-skill-cooldown-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=25,native=21,
    tests=['test_portable_skill_cooldown.py','test_portable_typed_recipient_delegation.py'])
SUITES['regression']=dict(script='research/verify-world-regression-short.py',
    golden='research/portable-world-revival-notify-regression-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=759,native=602,
    tests=['test_portable_regression_adapter.py','test_portable_roster_regression.py',
           'test_portable_readiness.py','test_portable_stun.py','test_portable_typed_recipient_delegation.py',
           'test_portable_skill_cooldown.py','test_portable_healing_storage.py','test_portable_trigger_reduction.py','test_portable_skill_critical.py','test_portable_skill_interval.py','test_portable_skill_interval_flat.py','test_portable_lazy_bank.py','test_portable_compiler_stats.py','test_portable_base_copy.py','test_portable_seal.py','test_portable_persona.py','test_portable_compile_cache.py','test_portable_named_magnitude.py','test_portable_enemy_selection.py','test_portable_capture_storage.py','test_portable_attack_magnitude.py','test_portable_revive_reference.py','test_portable_revival.py'])
SUITES['healing-storage']=dict(script='research/verify-world-healing-storage-short.py',
    golden='research/portable-world-healing-storage-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=51,native=39,development_only=True,
    tests=['test_portable_healing_storage.py'])
SUITES['roster-admission-diagnostic']=dict(script='research/verify-world-roster-regression-short.py',
    golden='research/portable-world-roster-regression-short-expected.json',
    source='gpu/world_projectile_admission_entry.slang',inputs=62,native=62,development_only=True,
    tests=['test_portable_real_binding_proof.py'])
SUITES['trigger-reduction']=dict(script='research/verify-world-trigger-reduction-short.py',
    golden='research/portable-world-trigger-reduction-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=48,native=40,development_only=True,
    tests=['test_portable_trigger_reduction.py'])
SUITES['skill-critical']=dict(script='research/verify-world-skill-critical-short.py',
    golden='research/portable-world-skill-critical-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=36,native=26,development_only=True,
    tests=['test_portable_skill_critical.py'])
SUITES['skill-interval']=dict(script='research/verify-world-skill-interval-short.py',
    golden='research/portable-world-skill-interval-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=32,native=28,development_only=True,
    tests=['test_portable_skill_interval.py'])
SUITES['skill-interval-flat']=dict(script='research/verify-world-skill-interval-flat-short.py',
    golden='research/portable-world-skill-interval-flat-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=57,native=40,development_only=True,
    tests=['test_portable_skill_interval_flat.py'])
SUITES['lazy-bank']=dict(script='research/verify-world-lazy-bank-short.py',
    golden='research/portable-world-lazy-bank-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=8,native=7,development_only=True,
    tests=['test_portable_lazy_bank.py','test_portable_compiler_stats.py'])
SUITES['base-copy']=dict(script='research/verify-world-base-copy-short.py',
    golden='research/portable-world-base-copy-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=47,native=32,development_only=True,
    tests=['test_portable_base_copy.py','test_portable_readiness.py'])
SUITES['persona']=dict(script='research/verify-world-persona-short.py',
    golden='research/portable-world-persona-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=41,native=25,development_only=True,
    tests=['test_portable_persona.py','test_portable_recipient_extension.py'])

SUITES['named-magnitude']=dict(script='research/verify-world-named-magnitude-short.py',
    golden='research/portable-world-named-magnitude-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=54,native=43,development_only=True,
    tests=['test_portable_named_magnitude.py','test_portable_readiness.py'])

SUITES['attack-magnitude']=dict(script='research/verify-world-attack-magnitude-short.py',
    golden='research/portable-world-attack-magnitude-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=52,native=42,development_only=True,
    tests=['test_portable_attack_magnitude.py','test_portable_named_magnitude.py','test_portable_readiness.py'])
SUITES['attack-magnitude-diagnostic']=dict(SUITES['attack-magnitude'],source='gpu/world_projectile_admission_entry.slang')

SUITES['enemy-selection']=dict(script='research/verify-world-enemy-selection-short.py',
    golden='research/portable-world-enemy-selection-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=60,native=51,development_only=True,
    tests=['test_portable_enemy_selection.py','test_portable_readiness.py'])

SUITES['enemy-selection-diagnostic']=dict(SUITES['enemy-selection'],source='gpu/world_projectile_admission_entry.slang',require_rejection_stage=True)
SUITES['roster-skill-diagnostic']=dict(SUITES['roster-admission-diagnostic'],source='gpu/world_projectile_skill_diagnostic_entry.slang')

SUITES['revive']=dict(script='research/verify-world-revive-short.py',golden='research/portable-world-revive-short-expected.json',source='gpu/world_projectile_entry.slang',inputs=35,native=26,development_only=True,tests=['test_portable_revive_reference.py','test_portable_revival.py'])
SUITES['revive-diagnostic']=dict(SUITES['revive'],source='gpu/world_projectile_admission_entry.slang',require_rejection_stage=True)

SCHEMA = 1
# Controller validation has no numeric program to execute. Keep its CPU work
# separate from a selected suite's battle/native preflight.
SMOKE_TESTS = ['test_portable_windows_cleanup.py','test_portable_gpu_cli.py',
               'test_portable_compile_cache.py','test_portable_cuda_artifact.py']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    """Atomic durable publication, including failures and partial-run status."""
    path = Path(path)
    temp = path.with_suffix(path.suffix+'.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path)


def safe_name(name):
    p = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or p.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')):
        raise ValueError('Unsafe artifact path')
    return name


def file_records(root, names):
    records = []
    for name in sorted(names):
        safe_name(name)
        p = root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError('Expected regular artifact: '+name)
        data = p.read_bytes()
        records.append(dict(path=name, bytes=len(data), sha256=sha(data)))
    return records


def check_records(root, records):
    names = [safe_name(r['path']) for r in records]
    if len(names) != len(set(names)) or file_records(root, names) != sorted(records, key=lambda r:r['path']):
        raise ValueError('Artifact bytes/SHA/size mismatch')


def package_id(manifest):
    body = {k:v for k,v in manifest.items() if k != 'package_id'}
    return sha(json.dumps(body, sort_keys=True, separators=(',', ':')).encode())


def verify_package(root):
    m = load(root/'gpu-package.json')
    if m['schema'] != SCHEMA or m['package_id'] != package_id(m) or m['suite'] not in SUITES:
        raise ValueError('Invalid package identity/schema/suite')
    if m.get('purpose','sealed') not in ('sealed','development') or (not is_development(m) and m.get('selected_cases')):
        raise ValueError('Invalid package purpose/case selection')
    check_records(root, m['files'])
    golden = m['golden'] if is_development(m) else load(root/SUITES[m['suite']]['golden'])
    if golden != m['golden']:
        raise ValueError('Package golden mismatch')
    return m


def make_package(suite, output, *, develop=False, cases=()):
    """Whitelist code + required public data; never reports/raw/settings/tools."""
    if SUITES[suite].get('development_only') and not develop:
        raise ValueError('This suite requires --develop until an explicit Metal seal is registered')
    tracked = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode().split('\0')
    names = []
    for name in filter(None, tracked):
        p = PurePosixPath(name)
        if ((p.parts[0] in ('app','gpu','scripts','research','tests') and p.suffix in ('.py','.slang','.swift'))
            or (p.parts[0]=='data' and p.suffix=='.json') or name==SUITES[suite]['golden']):
            names.append(name)
    # Include this CLI even before its first commit during local development.
    if 'scripts/nikke_gpu.py' not in names:
        names.append('scripts/nikke_gpu.py')
    for pattern in SUITES[suite]['tests']:
        if 'tests/'+pattern not in names:
            raise ValueError('Required CPU test is missing from tracked payload: '+pattern)
    upstream = ROOT/'research/upstream/nikke-calc-master'
    for folder in ('calculator','runner','scraper','data'):
        names.extend(p.relative_to(ROOT).as_posix() for p in (upstream/folder).rglob('*')
                     if p.is_file() and not p.is_symlink() and p.suffix in ('.py','.json'))
    license_path = upstream/'LICENSE'
    if not license_path.is_file() or not (upstream/'data/parsed_nikke.json').is_file():
        raise ValueError('Pinned upstream source/data must be installed first')
    names.append(license_path.relative_to(ROOT).as_posix())
    records = file_records(ROOT, names)
    if cases and not develop:
        raise ValueError('--case requires --develop')
    golden = development_baseline(suite, cases) if develop else load(ROOT/SUITES[suite]['golden'])
    # Early stale-golden detection, without importing native engine or building.
    for name, digest in golden['source_sha256'].items():
        if sha((ROOT/name).read_bytes()) != digest:
            raise ValueError('Golden GPU source is stale: '+name)
    m = dict(schema=SCHEMA, suite=suite,
             source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             working_tree_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
             files=records, golden=golden, purpose='development' if develop else 'sealed', selected_cases=list(cases), runtime_requirements=['Python dependencies from the existing venv', 'Slang 2026.20', 'CUDA toolkit/driver on Windows or Swift/Metal on macOS'])
    m['package_id'] = package_id(m)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('gpu-package.json', json.dumps(m, ensure_ascii=False, indent=2))
        for row in records:
            archive.writestr(row['path'], (ROOT/row['path']).read_bytes())
    return dict(package_id=m['package_id'], files=len(records), bytes=Path(output).stat().st_size,
                archive_sha256=sha(Path(output).read_bytes()), source_commit=m['source_commit'])


def unpack(archive, destination):
    # Validate every member before creating a destination. Never extractall().
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate package members')
        for name in names:
            safe_name(name)
        m = json.loads(z.read('gpu-package.json'))
        if m.get('schema')!=SCHEMA or not isinstance(m.get('suite'),str) or not m['suite']:
            raise ValueError('Unsupported package schema or missing suite identity')
        listed=[row['path'] for row in m['files']]
        if len(listed)!=len(set(listed)):
            raise ValueError('Duplicate package artifact records')
        if m['package_id'] != package_id(m) or set(names) != {'gpu-package.json', *(r['path'] for r in m['files'])}:
            raise ValueError('Unlisted package members or identity mismatch')
        for row in m['files']:
            raw = z.read(row['path'])
            if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
                raise ValueError('Package member integrity failure')
        destination.mkdir(parents=True, exist_ok=False)
        for name in names:
            p = destination/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(z.read(name))
    # Transfer integrity is independent of this bootstrap CLI's suite registry.
    # The extracted package's own CLI performs semantic preflight before run.
    check_records(destination,m['files'])
    return m['package_id']


def module(path):
    spec = importlib.util.spec_from_file_location('gpu_suite_adapter', path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def open_suite(m):
    return module(ROOT/SUITES[m['suite']]['script'])


def is_development(m):
    return m.get('purpose', 'sealed') == 'development'


def prepare_entries(adapter, m):
    entries, data = adapter.prepare()
    if is_development(m) and hasattr(adapter, 'development_entries'):
        entries = entries + adapter.development_entries()
        data = None
    selected = m.get('selected_cases', [])
    if not selected and data is not None:
        return entries, data
    names = [row[0] for row in entries]
    if len(set(selected)) != len(selected) or not set(selected) <= set(names):
        raise ValueError('Unknown or duplicate selected cases')
    entries = [row for row in entries if not selected or row[0] in selected]
    packed = array.array('I', [len(entries)])
    for _, words, _ in entries:
        packed.extend(words)
    if sys.byteorder != 'little': packed.byteswap()
    return entries, packed.tobytes()


def development_baseline(suite, cases):
    """Freeze inputs and native oracles without treating new GPU output as truth."""
    with forbid_gpu():
        m = dict(suite=suite, purpose='development', selected_cases=list(cases))
        adapter = open_suite(m)
        entries, data = prepare_entries(adapter, m)
        from portable_backend import source_hashes
        iw = adapter.suite.INPUT * 4
        return dict(input_sha256=sha(data), source_sha256=source_hashes(SUITES[suite]['source']),
                    entries=[dict(name=name, input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),
                                  native_sha256=native_hash(adapter, domain))
                             for i,(name,words,domain) in enumerate(entries)])


def native_hash(adapter, domain):
    if domain is None:
        value = dict(status=64)
    elif hasattr(adapter,'native_reference'):
        value = adapter.native_reference(domain)
    else:
        value = dict(zip(('battle','skill_trace'), adapter.suite.inspect_native(domain[0])))
    return adapter.cross.digest(value)


@contextlib.contextmanager
def forbid_gpu():
    import portable_backend
    def stop(*args, **kwargs):
        raise RuntimeError('GPU build/execute forbidden in CPU/audit stage')
    with patch.object(portable_backend,'build',stop), patch.object(portable_backend,'execute',stop), patch.object(portable_backend,'execute_batches',stop):
        yield


def cpu_preflight(m):
    started = time.perf_counter()
    (ROOT/'research/portable-build').mkdir(parents=True,exist_ok=True)
    # Patch before importing the adapter, so its from-import aliases are blocked.
    with forbid_gpu():
        adapter = open_suite(m)
        entries, data = prepare_entries(adapter, m)
        golden = m['golden']
        if sha(data) != golden['input_sha256'] or len(entries) != len(golden['entries']):
            raise ValueError('Input differs from golden')
        iw = adapter.suite.INPUT*4
        for i,(name,words,domain) in enumerate(entries):
            expected = golden['entries'][i]
            if (name != expected['name'] or sha(data[4+i*iw:4+(i+1)*iw]) != expected['input_sha256']
                or native_hash(adapter,domain) != expected['native_sha256']):
                raise ValueError('First CPU/input mismatch: '+name)
    from portable_typed_cuda_proof_audit import verify_cpu_gpu_calls
    calls = dict(build=0,execute=0); verify_cpu_gpu_calls(calls)
    return dict(passed=True, input_count=len(entries), native_oracles=sum(domain is not None for _,_,domain in entries),
                input_sha256=sha(data), gpu_calls=calls, elapsed_seconds=time.perf_counter()-started)


def child(capture, backend, smoke=False, compile_only=False):
    deadline = time.monotonic()+60
    while not (capture/'start.json').exists():
        if time.monotonic() >= deadline:
            raise RuntimeError('Containment gate not released; GPU not started')
        time.sleep(.02)
    if smoke:
        if compile_only:raise ValueError('Compile and smoke modes are exclusive')
        write(capture/'smoke.json',dict(pid=os.getpid(),ppid=os.getppid(),gpu_calls=0)); return
    m = verify_package(ROOT)
    if compile_only:
        compile_child(m,capture,backend);return
    adapter = open_suite(m)
    entries, data = prepare_entries(adapter, m)
    if sha(data) != m['golden']['input_sha256']:
        raise ValueError('Input changed after preflight')
    (capture/'input.bin').write_bytes(data)
    import portable_backend
    from portable_phase_audit import Journal, observe
    journal = Journal(capture/'phases.jsonl')
    with observe(portable_backend,journal):
        raw,evidence = journal.invoke('shared_gpu_execute',portable_backend.execute,
                                     SUITES[m['suite']]['source'],'portableEvents',data,
                                     adapter.suite.INPUT,786432,backend)
    # Raw/evidence are durable before any comparison, so failures remain inspectable.
    (capture/'readback.bin').write_bytes(raw); write(capture/'evidence.json',evidence)
    copy_generated(capture,m['suite'])
    result = journal.invoke('shared_native_compare',compare_readback,m,capture,adapter=adapter)
    write(capture/'comparison.json',result)
    if not result['calculation_verified']:
        raise ValueError('GPU comparison failed; see comparison.json')


def compare_readback(m, capture, adapter=None):
    """Re-run existing native comparators; no GPU builds/executes allowed."""
    (ROOT/'research/portable-build').mkdir(parents=True, exist_ok=True)
    with forbid_gpu():
        adapter = adapter or open_suite(m)
        entries,data = prepare_entries(adapter, m)
        raw=(capture/'readback.bin').read_bytes(); evidence=load(capture/'evidence.json')
        if (capture/'input.bin').read_bytes()!=data or sha(data)!=m['golden']['input_sha256']:
            raise ValueError('Saved input mismatch')
        if len(raw)!=len(entries)*786432*4 or sha(raw)!=evidence['output_sha256'] or evidence['input_sha256']!=sha(data):
            raise ValueError('Saved evidence/raw mismatch')
        if evidence['source_sha256']!=m['golden']['source_sha256'] or not evidence['gpu_execution_verified']:
            raise ValueError('Wrong/unverified GPU source')
        if evidence['backend']=='cuda' and 'compile_artifact' in evidence['transport']:
            receipt=evidence['transport']['compile_artifact'];kind=receipt['identity']['artifact']
            if kind not in ('ptx','cubin'):raise ValueError('Unknown compiled CUDA artifact')
            artifact=(capture/('compiled.'+kind)).read_bytes()
            identity_key=sha(json.dumps(receipt['identity'],sort_keys=True,separators=(',',':')).encode())
            if receipt['key']!=identity_key or receipt['identity']['artifact'] not in ('ptx','cubin') or receipt['identity']['schema']!=1:
                raise ValueError('Invalid CUDA compile cache key/schema')
            from portable_backend import cuda_compile_options
            allowed=[cuda_compile_options(kind)]
            if kind=='cubin':allowed += [cuda_compile_options(kind,level) for level in range(4)]
            if receipt['identity']['options'] not in allowed:
                raise ValueError('CUDA compiler options changed')
            if sha(artifact)!=receipt['artifact_sha256'] or len(artifact)!=receipt['artifact_bytes']:
                raise ValueError('Compiled CUDA artifact mismatch')
            if receipt['identity']['source_sha256']!=sha((capture/'generated.cu').read_bytes()):
                raise ValueError('Compiled CUDA source identity mismatch')
            phases=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
            if [r['receipt'] for r in phases if r['stage']=='cuda_compile_cache' and r['state']=='verified']!=[receipt]:
                raise ValueError('CUDA compiler artifact phase mismatch')
        results=[]; mismatches=[]; iw=adapter.suite.INPUT*4; ow=786432*4
        for i,(name,words,domain) in enumerate(entries):
            part=raw[i*ow:(i+1)*ow]; block=array.array('I'); block.frombytes(part)
            if sys.byteorder!='little': block.byteswap()
            try:
                if domain is None:
                    if block[0]!=64:raise ValueError('Expected rejection status64')
                    if hasattr(adapter,'validate_rejection'):adapter.validate_rejection(block,name)
                    if SUITES[m['suite']].get('require_rejection_stage'):adapter.validate_rejection_stage(block,name)
                    native=dict(status=64)
                else:
                    if block[0]!=0:raise ValueError('Expected GPU success status0; got status'+str(block[0]))
                    native=adapter.compare(block,domain)
                row=dict(name=name,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(part),native_sha256=adapter.cross.digest(native))
                expected = m['golden']['entries'][i]
                actual = {key:row[key] for key in expected} if is_development(m) else row
                if actual!=expected:mismatches.append(dict(index=i,name=name,reason='fingerprint mismatch'))
                results.append(row)
            except (AssertionError,ValueError,KeyError,IndexError) as error:
                mismatches.append(dict(index=i,name=name,reason=type(error).__name__+': '+str(error)))
        # Reuse strict normalizer; no new normalization exceptions.
        generated={}
        for backend,suffix in [('cuda','cu'),('metal','metal')]:
            generated[backend]=adapter.cross.normalized((capture/('generated.'+suffix)).read_bytes())
        if not is_development(m) and generated!=m['golden']['generated_normalized']:mismatches.append(dict(reason='generated code mismatch'))
        if not is_development(m) and sha(raw)!=m['golden']['output_sha256']:mismatches.append(dict(reason='full readback fingerprint mismatch'))
        return dict(calculation_verified=not mismatches, entries=results, mismatches=mismatches,
                    input_count=len(entries), native_oracles=sum(domain is not None for _,_,domain in entries),
                    input_sha256=sha(data),output_sha256=sha(raw),generated_normalized=generated,audit_gpu_calls=0)


def replay_source(m, source_package, source_capture):
    """Validate an immutable successful Metal dispatch, including failed decode."""
    original=verify_package(source_package)
    if not is_development(m) or not is_development(original) or m['suite']!=original['suite'] or m['golden']!=original['golden']:
        raise ValueError('Replay requires identical development source/input/native baselines')
    old={r['path']:r['sha256'] for r in original['files']};new={r['path']:r['sha256'] for r in m['files']}
    critical={'app/portable_backend.py','app/portable_compile_cache.py','scripts/run-metal-probe.swift',
              'research/portable_phase_audit.py','research/summarize-portable-cross-gpu.py',
              'app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py'}
    critical |= {name for name in old.keys() | new.keys() if name.startswith(('gpu/','research/upstream/'))}
    if any(name not in old or name not in new or old[name]!=new[name] for name in critical):
        raise ValueError('GPU transport, source, normalizer or canonical reference changed')
    run=load(source_capture/'run.json')
    if run['package_id']!=original['package_id'] or run['backend']!='metal' or run.get('mode')!='gpu':
        raise ValueError('Original Metal GPU capture required')
    claim=load(source_package/'gpu-claimed-metal.json')
    if claim['package_id']!=original['package_id'] or Path(claim['capture']).resolve()!=source_capture.resolve():
        raise ValueError('Original GPU execution claim mismatch')
    records=load(source_capture/'artifacts.json')['files']
    required={'run.json','execution.json','evidence.json','phases.jsonl','comparison.json','result.json'}
    if not required <= {r['path'] for r in records}:raise ValueError('Original capture proof set incomplete')
    check_records(source_capture,records)
    facts=load(source_capture/'execution.json');evidence=load(source_capture/'evidence.json')
    if facts['timed_out'] or any(facts[k] is not None for k in ('error','cleanup_error','observation_error')):
        raise ValueError('Timeout/control failure cannot be replayed as a completed dispatch')
    if facts['final_child_exit_code'] not in (0,1):raise ValueError('Unexpected original child termination')
    if evidence['backend']!='metal' or not evidence['gpu_execution_verified'] or evidence['transport']['command_status']!='completed':
        raise ValueError('Original dispatch did not complete on Metal')
    rows=[json.loads(line) for line in (source_capture/'phases.jsonl').read_text().splitlines()]
    dispatch=[r['state'] for r in rows if r['stage']=='shared_gpu_execute']
    if dispatch!=['entered','returned']:raise ValueError('Original GPU execution boundary incomplete')
    for backend,suffix in [('cuda','cu'),('metal','metal')]:
        if sha((source_capture/('generated.'+suffix)).read_bytes())!=evidence['generated_sha256'][backend]:
            raise ValueError('Original generated bytes mismatch')
    return original,facts,evidence


def audit_replay_capture(m, capture, *, verify_artifacts=True):
    run=load(capture/'run.json');origin=load(capture/'replay.json')
    if run['package_id']!=m['package_id'] or run['backend']!='metal':raise ValueError('Wrong replay package/backend')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    original,facts,evidence=replay_source(m,Path(origin['source_package']),Path(origin['source_capture']))
    if origin['source_package_id']!=original['package_id']:raise ValueError('Wrong original package')
    source=Path(origin['source_capture'])
    for name in ('input.bin','readback.bin','evidence.json','generated.cu','generated.metal'):
        if (capture/name).read_bytes()!=(source/name).read_bytes():raise ValueError('Replay changed original bytes: '+name)
    if (capture/'source-execution.json').read_bytes()!=(source/'execution.json').read_bytes():
        raise ValueError('Replay changed original failure/control facts')
    result=compare_readback(m,capture)
    return dict(result,passed=result['calculation_verified'],preservation_verified=None,sealed=False,
                mode='saved-metal-replay',source_package_id=original['package_id'],source_execution_passed=facts['passed'],
                original_failure_preserved=True,gpu_calls=0,gpu_retry_count=0,source_gpu_dispatches=1)


def replay_capture(capture, source_package, source_capture):
    m=verify_package(ROOT);original,facts,evidence=replay_source(m,source_package,source_capture)
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend='metal',mode='replay',status='replaying',gpu_retry_count=0))
    write(capture/'replay.json',dict(source_package=str(source_package.resolve()),source_capture=str(source_capture.resolve()),source_package_id=original['package_id']))
    for name in ('input.bin','readback.bin','evidence.json','generated.cu','generated.metal'):
        (capture/name).write_bytes((source_capture/name).read_bytes())
    (capture/'source-execution.json').write_bytes((source_capture/'execution.json').read_bytes())
    try:
        result=audit_replay_capture(m,capture,verify_artifacts=False)
        write(capture/'comparison.json',compare_readback(m,capture));write(capture/'result.json',result)
        run=load(capture/'run.json');run['status']='finished';write(capture/'run.json',run)
    except BaseException as error:
        write(capture/'failure.json',dict(error=type(error).__name__+': '+str(error),gpu_calls=0));raise
    finally:collect(capture,capture/'artifacts.json')
    return result


def compiler_statistics(capture,output,*,top=12,caller=None,runtime=None):
    """Inspect a saved generated source with the existing artifact verifier."""
    if output.exists():raise ValueError('Compiler statistics output already exists')
    records=load(capture/'artifacts.json')['files']
    source=[r for r in records if r['path']=='generated.cu']
    if len(source)>1:raise ValueError('Duplicate generated CUDA source records')
    if source:check_records(capture,source)
    raw=(capture/'generated.cu').read_bytes()
    from portable_compiler_stats import cuda_statistics
    result=cuda_statistics(raw,top=top,caller=caller,runtime=runtime)
    anchored=bool(source)
    for name in ('evidence.json','compiler.json'):
        if (capture/name).is_file():
            record=[r for r in records if r['path']==name]
            if len(record)!=1:raise ValueError('Source evidence record missing')
            check_records(capture,record)
            if load(capture/name)['generated_sha256']['cuda']!=result['source_sha256']:
                raise ValueError('Generated CUDA does not match source evidence')
            anchored=True
    if not anchored:raise ValueError('Saved generated-source hash evidence required')
    result.update(source_integrity_verified=True,analysis_complete=True,
                  calculation_verified=False,compiler_verified=False,
                  gpu_calls=0,nvrtc_compile_calls=0)
    write(output,result);return result


def ptx_statistics(cache_entry,phases,output,*,top=8):
    if output.exists():raise ValueError('PTX statistics output already exists')
    from portable_ptx_stats import saved_ptx_statistics
    result=saved_ptx_statistics(cache_entry,phases,top=top)
    write(output,result);return result


def check_compile_cache(capture, output):
    """Verify warm artifact reuse using file reads only: NVRTC/GPU forbidden."""
    m=verify_package(ROOT)
    if load(capture/'run.json')['package_id']!=m['package_id']:
        raise ValueError('Capture belongs to another package')
    check_records(capture,load(capture/'artifacts.json')['files'])
    if load(capture/'run.json')['backend']!='cuda':raise ValueError('CUDA artifact required')
    evidence=load(capture/'evidence.json') if (capture/'evidence.json').exists() else None
    from portable_compile_cache import get_or_compile,quoted_headers
    directory=os.environ.get('NIKKE_CUDA_COMPILE_CACHE')
    if not directory:raise ValueError('NIKKE_CUDA_COMPILE_CACHE is required')
    cuda_bin=Path(os.environ.get('CUDA_PATH',r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3'))/'bin'
    if evidence is not None:receipt=evidence['transport']['compile_artifact']
    else:
        receipts=[]
        lines=(capture/'phases.jsonl').read_text().splitlines()
        for i,line in enumerate(lines):
            try:row=json.loads(line)
            except json.JSONDecodeError:
                if i!=len(lines)-1:raise
                continue
            if row['stage']=='cuda_compile_cache' and row['state']=='verified':receipts.append(row['receipt'])
        if len(receipts)!=1:raise ValueError('No unique successful compiler artifact')
        receipt=receipts[0]
    def forbidden():raise RuntimeError('Cache miss; NVRTC compilation forbidden in cache-check')
    started=time.perf_counter()
    artifact,hit=get_or_compile((capture/'generated.cu').read_bytes(),receipt['identity']['options'],
                               list(cuda_bin.glob('nvrtc*.dll')),forbidden,directory,
                               header_files=quoted_headers((capture/'generated.cu').read_bytes()),
                               artifact_kind=receipt['identity']['artifact'])
    if not hit['hit'] or hit['key']!=receipt['key'] or artifact!=(capture/('compiled.'+receipt['identity']['artifact'])).read_bytes():
        raise ValueError('Warm CUDA artifact does not match captured compiler output')
    result=dict(passed=True,cache=hit,elapsed_seconds=time.perf_counter()-started,
                gpu_calls=0,nvrtc_compile_calls=0,calculation_verified=False,package_id=m['package_id'])
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    return result


def audited_comparison(module, capture):
    """Use the original comparator's result from this fresh independent audit."""
    observed=[]
    original=module.compare_readback
    def compare(*args,**kwargs):
        result=original(*args,**kwargs)
        observed.append(result)
        return result
    with patch.object(module,'compare_readback',compare):
        audit=module.audit_capture(capture)
    if not audit['calculation_verified'] or len(observed)!=1:
        raise ValueError('Seal requires exactly one successful independent comparison')
    return audit,observed[0]


def seal_development(package_root, capture, output):
    """Explicit GPU0 seal of a successful immutable Metal development capture."""
    # Use the package's own imports and auditors in a fresh process. Its files
    # are verified before native work; never patch a consumed package in place.
    script = """import importlib.util,json,sys,pathlib
root=pathlib.Path(sys.argv[1]);capture=pathlib.Path(sys.argv[2])
s=importlib.util.spec_from_file_location('seal_controller',sys.argv[3])
controller=importlib.util.module_from_spec(s);s.loader.exec_module(controller)
s=importlib.util.spec_from_file_location('seal_cli',root/'scripts/nikke_gpu.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=m.verify_package(root)
if not m.is_development(p) or m.load(capture/'run.json')['backend']!='metal':raise ValueError('Metal development capture required')
a,r=controller.audited_comparison(m,capture)
g=dict(input_sha256=r['input_sha256'],output_sha256=r['output_sha256'],source_sha256=p['golden']['source_sha256'],entries=r['entries'],generated_normalized=r['generated_normalized'])
print(json.dumps(dict(golden=g,package_id=p['package_id'],audit=a)))
"""
    completed=subprocess.run([sys.executable,'-c',script,str(package_root.resolve()),str(capture.resolve()),str(Path(__file__).resolve())],
                             capture_output=True,text=True,check=True,timeout=60)
    result=json.loads(completed.stdout)
    for name,digest in result['golden']['source_sha256'].items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError('Current source differs from verified Metal source')
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result['golden'],stream,ensure_ascii=False,indent=2);stream.write('\n')
    return dict(sealed=True,gpu_calls=0,package_id=result['package_id'],
                input_count=len(result['golden']['entries']),golden=str(output.resolve()))


def copy_generated(capture, suite, *, partial=False):
    stem=Path(SUITES[suite]['source']).stem
    for suffix in ('cu','metal'):
        source=ROOT/'research/portable-build'/(stem+'.'+suffix)
        if source.exists():(capture/('generated.'+suffix)).write_bytes(source.read_bytes())
        elif not partial:raise ValueError('Missing generated source: '+suffix)
    for kind in ('ptx','cubin'):
        source=ROOT/'research/portable-build'/(stem+'.'+kind)
        if source.exists():(capture/('compiled.'+kind)).write_bytes(source.read_bytes())


def bounded_module():
    return module(ROOT/'research/run-world-bounded.py')


def validation_environment(capture):
    """Keep owned Windows tests/compiler scratch out of a sandbox default TEMP."""
    env=os.environ.copy();env.pop('__PYVENV_LAUNCHER__',None)
    if os.name=='nt':
        temporary=(capture/'temporary').resolve();temporary.mkdir(exist_ok=True)
        for key in ('TEMP','TMP','TMPDIR'):env[key]=str(temporary)
    return env


def run_job(capture,backend,timeout,original_workspace=None,smoke=False,compile_only=False):
    bounded=bounded_module()
    env=validation_environment(capture)
    env['PYTHONPATH']=os.pathsep.join([*site.getsitepackages(),env.get('PYTHONPATH','')])
    interpreter=getattr(sys,'_base_executable',sys.executable) if os.name=='nt' else sys.executable
    command=[interpreter,str(Path(__file__).resolve()),'_child','--capture',str(capture),'--backend',backend]
    if smoke:command.append('--smoke')
    if compile_only:command.append('--compile-only')
    write(capture/'runtime.json',dict(interpreter=interpreter,parent_interpreter=sys.executable,platform=platform.platform(),slang_root=os.environ.get('NIKKE_SLANG_ROOT'),cuda_artifact_kind=os.environ.get('NIKKE_CUDA_ARTIFACT','cubin') if backend=='cuda' else None,compile_cache_enabled=bool(os.environ.get('NIKKE_CUDA_COMPILE_CACHE')),compile_only=compile_only,ptxas_optimization_level=os.environ.get('NIKKE_CUDA_PTXAS_OPT_LEVEL'),cache_required=os.environ.get('NIKKE_CUDA_CACHE_REQUIRED','0'),job_memory_limit_mb=os.environ.get('NIKKE_VALIDATION_JOB_MEMORY_MB'),launcher_variable_removed='__PYVENV_LAUNCHER__' not in env))
    observation={}
    if os.name=='nt':
        from windows_validation_observer import capture_snapshot,observe_job,compare_snapshots
        if not original_workspace:raise ValueError('--original-workspace is required on Windows')
        def before():
            observation['before']=capture_snapshot(original_workspace,ROOT)
            write(capture/'observation.json',observation)
        def after():
            observation['after']=capture_snapshot(original_workspace,ROOT)
            if 'before' in observation:observation['comparison']=compare_snapshots(observation['before'],observation['after'])
            write(capture/'observation.json',observation)
        with observe_job(bounded,capture/'job.json'):
            facts=bounded.run_bounded(command,capture,timeout,cwd=ROOT,env=env,before_gate=before,after_wait=after)
    else:facts=bounded.run_bounded(command,capture,timeout,cwd=ROOT,env=env)
    return facts


def run_capture(capture,backend,timeout,original_workspace=None,smoke=False,cpu_only=False):
    m=verify_package(ROOT)
    if is_development(m) and backend!='metal':raise ValueError('Development execution requires Metal; seal before CUDA verification')
    if not 1<=timeout<=180:raise ValueError('Timeout must be 1..180')
    if backend=='cuda' and os.name!='nt' and not smoke and not cpu_only:raise ValueError('CUDA transport requires Windows')
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend=backend,
                                mode='cpu-only' if cpu_only else 'smoke' if smoke else 'gpu',status='preflight',gpu_retry_count=0))
    try:
        # An extracted packet deliberately excludes compiler distributions.
        # Catch a missing Metal toolchain before expensive native preparation
        # and before consuming the exclusive GPU execution claim.
        if backend=='metal' and not smoke and not cpu_only:
            compiler_root=Path(os.environ.get('NIKKE_SLANG_ROOT',ROOT/f'.tools/slang-2026.20-{platform.system()}-{platform.machine()}')).resolve()
            compiler=compiler_root/'bin'/('slangc.exe' if os.name=='nt' else 'slangc')
            if not compiler.is_file():
                raise ValueError('Slang compiler missing: '+str(compiler)+'; specify --slang-root')
        pre=(dict(passed=True,controller_only=True,input_count=0,native_oracles=0,gpu_calls=0)
             if smoke else cpu_preflight(m))
        write(capture/'cpu.json',pre)
        test_results=[]
        test_env=validation_environment(capture)
        for pattern in (SMOKE_TESTS if smoke else SUITES[m['suite']]['tests']):
            if not (ROOT/'tests'/pattern).is_file():raise ValueError('CPU test file missing: '+pattern)
            started=time.perf_counter()
            completed=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-p',pattern],cwd=ROOT,capture_output=True,timeout=60,env=test_env)
            (capture/(pattern+'.stdout.log')).write_bytes(completed.stdout)
            (capture/(pattern+'.stderr.log')).write_bytes(completed.stderr)
            test_results.append(dict(pattern=pattern,exit_code=completed.returncode,elapsed_seconds=time.perf_counter()-started))
            write(capture/'cpu-tests.json',test_results)
            if completed.returncode:raise ValueError('CPU tests failed: '+pattern)
        if cpu_only:
            write(capture/'result.json',dict(cpu_verified=True,gpu_calls=0,calculation_verified=False,preservation_verified=None,status='cpu-only'))
        else:
            # Durable exclusive claim prevents same-package/backend GPU retries, even after a crash.
            if not smoke:
                claim=ROOT/('gpu-claimed-'+backend+'.json')
                with claim.open('x',encoding='utf-8') as stream:
                    json.dump(dict(capture=str(capture),package_id=m['package_id'],started_unix_ns=time.time_ns()),stream)
            facts=run_job(capture,backend,timeout,original_workspace,smoke)
            if not smoke:
                # Child publishes generated files before comparing; failed compilation may lack them.
                copy_generated(capture,m['suite'],partial=True)
                result=audit_capture(capture,verify_artifacts=False)
            else:
                marker=load(capture/'smoke.json') if (capture/'smoke.json').exists() else {}
                smoke_ok=facts['passed']
                if os.name=='nt':
                    jobs=load(capture/'job.json')['records']
                    smoke_ok &= bool(len(jobs)==1 and jobs[0]['pre_gate_verified'] and not jobs[0]['inspection_error'] and jobs[0]['post_wait'] and jobs[0]['post_wait']['job_members']==[] and marker==dict(pid=jobs[0]['child_pid'],ppid=jobs[0]['wrapper_pid'],gpu_calls=0))
                result=dict(smoke_verified=bool(smoke_ok),gpu_calls=0,calculation_verified=False,preservation_verified=None,status='smoke')
            write(capture/'result.json',result)
        run=load(capture/'run.json');run.update(status='finished',finished_unix_ns=time.time_ns());write(capture/'run.json',run)
    except BaseException as error:
        write(capture/'failure.json',dict(error=type(error).__name__+': '+str(error),gpu_retries=0))
        run=load(capture/'run.json');run['status']='failed';write(capture/'run.json',run)
        raise
    finally:
        collect(capture,capture/'artifacts.json')
    return load(capture/'result.json')


def job_contained(capture,rows,*,memory_limit_bytes=None):
    if not (capture/'job.json').exists() or not rows:return False,None
    records=load(capture/'job.json')['records']
    if len(records)!=1:return False,None
    r=records[0];pre=r['pre_gate'];post=r['post_wait'];pid=r['child_pid']
    good=bool(r['pre_gate_verified'] and not r['inspection_error'] and pre and post
        and pre['child_pid']==post['child_pid']==pid
        and pre['child_ppid']==post['child_ppid']==r['wrapper_pid']
        and pre['job_members']==[pid] and post['job_members']==[]
        and bool(pre['child_creation_filetime_ticks'])
        and pre['child_creation_filetime_ticks']==post['child_creation_filetime_ticks']
        and all(row.get('pid')==pid for row in rows)
        and all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(rows,rows[1:]))
        and pre['observed_unix_ns']<=rows[0]['wall_time_ns']<=rows[-1]['wall_time_ns']<=post['observed_unix_ns'])
    if memory_limit_bytes is not None:
        good &= pre.get('job_memory_limit_bytes')==post.get('job_memory_limit_bytes')==memory_limit_bytes
    return bool(good),pid


def compile_child(m,capture,backend):
    """Same compiler/cache as execution, with no CUDA driver admission."""
    if backend!='cuda' or is_development(m):raise ValueError('Compile-only requires a sealed CUDA package')
    import portable_backend
    from portable_phase_audit import Journal,observe
    journal=Journal(capture/'phases.jsonl')
    loader=getattr(portable_backend.C,'WinDLL',None)
    def guarded_library(name,*args,**kwargs):
        basename=str(name).replace('\\','/').rsplit('/',1)[-1].lower()
        if not basename.startswith('nvrtc') or not basename.endswith('.dll'):
            journal.emit('cuda_driver_load_forbidden','rejected');raise RuntimeError('Only the NVRTC compiler library is allowed')
        journal.emit('cuda_compiler_library','loaded',name=basename)
        return loader(name,*args,**kwargs)
    def forbidden(*a,**k):raise RuntimeError('GPU dispatch forbidden in compile-only mode')
    with patch.object(portable_backend.C,'WinDLL',guarded_library,create=True),patch.object(portable_backend,'execute',forbidden),patch.object(portable_backend,'execute_batches',forbidden),observe(portable_backend,journal):
        outputs,hashes=portable_backend.build(SUITES[m['suite']]['source'],'portableEvents')
        normalized=module(ROOT/'research/summarize-portable-cross-gpu.py').normalized
        generated={k:normalized(p.read_bytes()) for k,p in outputs.items()}
        if hashes!=m['golden']['source_sha256'] or generated!=m['golden']['generated_normalized']:
            raise ValueError('Generated compiler inputs differ from the sealed Metal proof')
        artifact,receipt=journal.invoke('shared_cuda_compile_only',portable_backend.compile_cuda_source,outputs['cuda'])
    copy_generated(capture,m['suite'])
    write(capture/'compiler.json',dict(source_sha256=hashes,generated_sha256={k:sha(p.read_bytes()) for k,p in outputs.items()},
        generated_normalized=generated,compile_artifact=receipt,gpu_calls=0,driver_load_calls=0,calculation_verified=False))


def audit_compile_capture(m,capture,*,verify_artifacts=True):
    run=load(capture/'run.json')
    if run.get('mode')!='compile-only' or run['package_id']!=m['package_id'] or run['backend']!='cuda':raise ValueError('Wrong compiler capture')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    facts=load(capture/'execution.json')
    if is_development(m) or type(facts['timeout_seconds']) is not int or not 1<=facts['timeout_seconds']<=60 or type(run['memory_limit_mb']) is not int or not 64<=run['memory_limit_mb']<=4096:raise ValueError('Compiler proof exceeds its bounded policy')
    rows=[];phase_error=None
    if (capture/'phases.jsonl').exists():
        for line in (capture/'phases.jsonl').read_text().splitlines():
            try:rows.append(json.loads(line))
            except json.JSONDecodeError:phase_error='Malformed or incomplete compiler phase journal';break
    complete=phase_error is None and [r['state'] for r in rows if r['stage']=='shared_cuda_compile_only']==['entered','returned']
    no_gpu=not any((r['stage'].startswith('cu') and len(r['stage'])>2 and r['stage'][2].isupper()) or r['stage'] in ('shared_gpu_execute','cuda_driver_load_forbidden') for r in rows)
    compiler=False;error=phase_error
    if (capture/'compiler.json').exists():
        try:
            c=load(capture/'compiler.json');receipt=c['compile_artifact'];kind=receipt['identity']['artifact']
            if kind!=run['artifact_kind']:raise ValueError('Compiler artifact kind mismatch')
            from portable_backend import cuda_compile_options
            if receipt['identity']['options']!=cuda_compile_options(kind,run['ptxas_level']):raise ValueError('Compiler options mismatch')
            if c['source_sha256']!=m['golden']['source_sha256'] or c['generated_normalized']!=m['golden']['generated_normalized']:raise ValueError('Compiler source baseline mismatch')
            normalized=module(ROOT/'research/summarize-portable-cross-gpu.py').normalized
            for backend,suffix in [('cuda','cu'),('metal','metal')]:
                raw=(capture/('generated.'+suffix)).read_bytes()
                if sha(raw)!=c['generated_sha256'][backend] or normalized(raw)!=c['generated_normalized'][backend]:raise ValueError('Compiler generated bytes mismatch')
            artifact=(capture/('compiled.'+kind)).read_bytes()
            if sha(artifact)!=receipt['artifact_sha256'] or len(artifact)!=receipt['artifact_bytes']:raise ValueError('Compiler output mismatch')
            if kind=='cubin' and not artifact.startswith(b'\x7fELF'):raise ValueError('Compiler output is not ELF')
            if receipt['identity']['source_sha256']!=c['generated_sha256']['cuda']:raise ValueError('Compiler input mismatch')
            if receipt['key']!=sha(json.dumps(receipt['identity'],sort_keys=True,separators=(',',':')).encode()):raise ValueError('Compiler identity key mismatch')
            if [r['receipt'] for r in rows if r['stage']=='cuda_compile_cache' and r['state']=='verified']!=[receipt]:raise ValueError('Compiler receipt phase mismatch')
            compiler=True
        except (ValueError,KeyError,OSError) as exc:error=str(exc)
    containment,pid=job_contained(capture,rows,memory_limit_bytes=run['memory_limit_mb']*1024*1024)
    from portable_phase_audit import summarize
    phase=summarize(capture/'phases.jsonl')
    compiler=bool(compiler and facts['passed'] and complete and no_gpu and containment and (phase['nvrtc_compile_returned_success'] or phase['cuda_compile_cache_hit_verified']))
    preservation=environment_preserved(capture,facts)
    return dict(mode='compile-only',compiler_verified=compiler,passed=compiler and preservation is True,
        containment_verified=containment,preservation_verified=preservation,calculation_verified=False,
        gpu_calls=0 if no_gpu else None,driver_load_calls=0 if no_gpu else None,phase=phase,error=error,gpu_retry_count=0)


def compile_capture(capture,timeout,original_workspace,artifact_kind='cubin',ptxas_level=None,memory_limit_mb=2048):
    if os.name!='nt':raise ValueError('Compile-only requires Windows')
    if type(timeout) is not int or not 1<=timeout<=60:raise ValueError('Compile-only budget must be1..60 seconds')
    if type(memory_limit_mb) is not int or not 64<=memory_limit_mb<=4096:raise ValueError('Compile-only memory must be64..4096 MiB')
    from portable_backend import cuda_compile_options
    cuda_compile_options(artifact_kind,ptxas_level)
    if not original_workspace or not os.environ.get('NIKKE_CUDA_COMPILE_CACHE'):raise ValueError('Original workspace and dedicated compiler cache required')
    m=verify_package(ROOT)
    if is_development(m):raise ValueError('Compile-only requires a sealed Metal package')
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend='cuda',mode='compile-only',status='compiling',artifact_kind=artifact_kind,ptxas_level=ptxas_level,memory_limit_mb=memory_limit_mb,gpu_retry_count=0))
    try:
        with (ROOT/'compile-claimed-cuda.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(package_id=m['package_id'],capture=str(capture),artifact_kind=artifact_kind,ptxas_level=ptxas_level),stream)
        environment=dict(NIKKE_CUDA_ARTIFACT=artifact_kind,NIKKE_CUDA_PTXAS_OPT_LEVEL='' if ptxas_level is None else str(ptxas_level),NIKKE_VALIDATION_JOB_MEMORY_MB=str(memory_limit_mb))
        with patch.dict(os.environ,environment):run_job(capture,'cuda',timeout,original_workspace,compile_only=True)
        copy_generated(capture,m['suite'],partial=True)
        result=audit_compile_capture(m,capture,verify_artifacts=False);write(capture/'result.json',result)
        run=load(capture/'run.json');run['status']='finished';write(capture/'run.json',run)
    except BaseException as exc:
        write(capture/'failure.json',dict(error=type(exc).__name__+': '+str(exc),gpu_calls=0))
        run=load(capture/'run.json');run['status']='failed';write(capture/'run.json',run);raise
    finally:collect(capture,capture/'artifacts.json')
    return result


def environment_preserved(capture,facts,backend='cuda'):
    preservation=None if backend!='cuda' else False
    if (capture/'observation.json').exists():
        from windows_validation_observer import compare_snapshots
        o=load(capture/'observation.json')
        if 'before' in o and 'after' in o:
            comparison=compare_snapshots(o['before'],o['after'])
            if o.get('comparison')!=comparison:raise ValueError('Process comparison mismatch')
            immediate=0 <= o['after']['observed_unix_ns']-facts['wait_completed_unix_ns'] <= 30_000_000_000
            preservation=bool(immediate and not facts['observation_error'] and comparison['all_monitored_processes_preserved'] and comparison['identified_nikke_service_preservation_verified'])
    return preservation


def audit_capture(capture,verify_artifacts=True):
    m=verify_package(ROOT)
    if load(capture/'run.json')['package_id']!=m['package_id']:raise ValueError('Capture belongs to another package')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    if load(capture/'run.json').get('mode')=='compile-only':
        return audit_compile_capture(m,capture,verify_artifacts=verify_artifacts)
    if load(capture/'run.json').get('mode')=='replay':
        return audit_replay_capture(m,capture,verify_artifacts=verify_artifacts)
    facts=load(capture/'execution.json')
    calc=False;error=None;first_difference=None
    if (capture/'readback.bin').exists():
        try:
            comparison=compare_readback(m,capture);calc=comparison['calculation_verified']
            first_difference=next(iter(comparison['mismatches']),None)
        except Exception as exc:error=type(exc).__name__+': '+str(exc)
    backend=load(capture/'run.json')['backend']
    if (capture/'evidence.json').exists():
        e=load(capture/'evidence.json')
        calc &= bool(e['backend']==backend and e['transport']['command_status']=='completed' and e['transport']['cases']==len(m['golden']['entries']))
    from portable_phase_audit import summarize,verify_cuda_trace
    phases=summarize(capture/'phases.jsonl')
    transport_ok=facts['passed']
    if backend=='cuda':
        transport_ok &= (phases['nvrtc_compile_returned_success'] or phases['cuda_compile_cache_hit_verified']) and all(phases[k] for k in ('cuda_launch_returned_success','cuda_synchronize_returned_success','cuda_readback_returned_success'))
    preservation=None if backend!='cuda' else False
    preservation=environment_preserved(capture,facts,backend)
    containment=True if backend!='cuda' else False
    if backend=='cuda':
        phase_rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()] if (capture/'phases.jsonl').exists() else []
        containment,pid=job_contained(capture,phase_rows)
        containment &= verify_cuda_trace(phase_rows,pid=pid) if containment else False
    return dict(sealed=not is_development(m),purpose=m.get('purpose','sealed'),
                calculation_verified=bool(calc and transport_ok and containment),preservation_verified=preservation,
                passed=bool(calc and transport_ok and containment and (backend!='cuda' or preservation is True)),
                containment_verified=containment,comparison_error=error,first_difference=first_difference,phase=phases,gpu_retries=0,audit_gpu_calls=0)


def collect(capture,output):
    # Raw remains local; return the small evidence/report set by default.
    names=[p.relative_to(capture).as_posix() for p in capture.iterdir()
           if p.is_file() and p.suffix in ('.json','.jsonl','.log') and p.name not in ('artifacts.json',Path(output).name)]
    result=dict(schema=SCHEMA,files=file_records(capture,names),raw_included=False,gpu_calls=0)
    write(output,result);return result


def export_results(capture,output):
    receipt=load(capture/'artifacts.json');check_records(capture,receipt['files'])
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('artifacts.json',json.dumps(receipt,indent=2))
        for row in receipt['files']:z.writestr(row['path'],(capture/row['path']).read_bytes())
    return dict(bytes=Path(output).stat().st_size,sha256=sha(Path(output).read_bytes()),gpu_calls=0)


def import_results(archive,destination):
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate result members')
        for name in names:safe_name(name)
        receipt=json.loads(z.read('artifacts.json'))
        if set(names)!={'artifacts.json',*(r['path'] for r in receipt['files'])}:raise ValueError('Unexpected result members')
        for row in receipt['files']:
            b=z.read(row['path'])
            if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise ValueError('Result integrity mismatch')
        destination.mkdir(parents=True,exist_ok=False)
        for name in names:
            p=destination/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    check_records(destination,receipt['files'])
    return dict(files=len(receipt['files']),gpu_calls=0,remote_report_only=True)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    a=sub.add_parser('replay');a.add_argument('--source-package',type=Path,required=True);a.add_argument('--source-capture',type=Path,required=True);a.add_argument('--capture',type=Path,required=True)
    a=sub.add_parser('cache-check');a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('compiler-stats');a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--top',type=int,default=12);a.add_argument('--caller');a.add_argument('--runtime')
    a=sub.add_parser('ptx-stats');a.add_argument('--cache-entry',type=Path,required=True);a.add_argument('--phases',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--top',type=int,default=8)
    a=sub.add_parser('compile');a.add_argument('--capture',type=Path,required=True);a.add_argument('--timeout',type=int,default=60)
    a.add_argument('--original-workspace',type=Path,required=True);a.add_argument('--artifact-kind',choices=('cubin','ptx'),default='cubin')
    a.add_argument('--ptxas-level',type=int,choices=range(4));a.add_argument('--memory-limit-mb',type=int,default=2048);a.add_argument('--slang-root',type=Path);a.add_argument('--compile-cache',type=Path)
    a=sub.add_parser('seal');a.add_argument('--package-root',type=Path,required=True);a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('cases');a.add_argument('--suite',choices=SUITES,required=True)
    a=sub.add_parser('inventory');a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('reference');a.add_argument('--suite',choices=('revive',),required=True);a.add_argument('--out',type=Path,required=True)
    for storage_command in ('archive-raw','restore-raw'):
        a=sub.add_parser(storage_command);a.add_argument('--capture',type=Path,required=True);a.add_argument('--archive',type=Path,required=True)
        if storage_command=='archive-raw':a.add_argument('--remove-original',action='store_true')
    a=sub.add_parser('package');a.add_argument('--suite',choices=SUITES,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--develop',action='store_true');a.add_argument('--case',action='append',default=[])
    a=sub.add_parser('unpack');a.add_argument('--archive',type=Path,required=True);a.add_argument('--dest',type=Path,required=True)
    for name in ('run','_child'):
        a=sub.add_parser(name);a.add_argument('--capture',type=Path,required=True);a.add_argument('--backend',choices=('metal','cuda'),required=True);a.add_argument('--smoke',action='store_true')
        if name=='run':
            a.add_argument('--cpu-only',action='store_true');a.add_argument('--timeout',type=int,default=180);a.add_argument('--original-workspace',type=Path);a.add_argument('--slang-root',type=Path)
            a.add_argument('--require-cache',action='store_true');a.add_argument('--compile-cache',type=Path);a.add_argument('--ptxas-level',type=int,choices=range(4));a.add_argument('--artifact-kind',choices=('cubin','ptx'))
        else:a.add_argument('--compile-only',action='store_true')
    for name in ('status','audit','collect','export'):
        a=sub.add_parser(name);a.add_argument('--capture',type=Path,required=True)
        if name in ('collect','export'):a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('import');a.add_argument('--archive',type=Path,required=True);a.add_argument('--dest',type=Path,required=True)
    a=sub.add_parser('audit-legacy');a.add_argument('--version',type=int,choices=(102,103,104),required=True)
    a=p.parse_args(argv)
    if hasattr(a,'capture'):a.capture=a.capture.resolve()
    if a.command=='list':
        result={}
        for name,config in SUITES.items():
            if not (ROOT/config['golden']).is_file():
                result[name]=dict(config,golden_source_ready=False,reason='No sealed golden');continue
            golden=load(ROOT/config['golden'])
            stale=[f for f,h in golden['source_sha256'].items() if not (ROOT/f).is_file() or sha((ROOT/f).read_bytes())!=h]
            result[name]=dict(config,golden_source_ready=not stale,stale_source_files=stale)
    elif a.command=='replay':result=replay_capture(a.capture,a.source_package,a.source_capture)
    elif a.command=='cache-check':result=check_compile_cache(a.capture,a.out)
    elif a.command=='compiler-stats':result=compiler_statistics(a.capture,a.out,top=a.top,caller=a.caller,runtime=a.runtime)
    elif a.command=='ptx-stats':result=ptx_statistics(a.cache_entry,a.phases,a.out,top=a.top)
    elif a.command=='compile':
        if a.slang_root:os.environ['NIKKE_SLANG_ROOT']=str(a.slang_root.resolve())
        if a.compile_cache:os.environ['NIKKE_CUDA_COMPILE_CACHE']=str(a.compile_cache.resolve())
        result=compile_capture(a.capture,a.timeout,a.original_workspace,a.artifact_kind,a.ptxas_level,a.memory_limit_mb)
    elif a.command=='seal':result=seal_development(a.package_root,a.capture,a.out)
    elif a.command=='cases':
        with forbid_gpu():
            entries,_=prepare_entries(open_suite(dict(suite=a.suite)),dict(purpose='development'))
        result=dict(suite=a.suite,cases=[row[0] for row in entries],gpu_calls=0)
    elif a.command=='inventory':
        if a.out.exists():raise ValueError('Inventory output already exists')
        inventory=module(ROOT/'research/audit-world-roster-input.py').main(destination=str(a.out.resolve()),quiet=True)
        result={k:inventory[k] for k in ('profile_count','packed_profiles','packed_base','forbidden_calls','classification')}
        result['report']=str(a.out.resolve());result['priority_categories']=len(inventory['priorities'])
    elif a.command=='reference':
        from portable_reference import run_reference
        result=run_reference(a.suite,a.out,write=write,forbid_gpu=forbid_gpu)
    elif a.command=='archive-raw':
        from portable_capture_storage import archive_raw
        result=archive_raw(a.capture,a.archive,check_records,remove_original=a.remove_original)
    elif a.command=='restore-raw':
        from portable_capture_storage import restore_raw
        result=restore_raw(a.capture,a.archive,check_records)
    elif a.command=='package':result=make_package(a.suite,a.out,develop=a.develop,cases=a.case)
    elif a.command=='unpack':result=dict(package_id=unpack(a.archive,a.dest))
    elif a.command=='run':
        if a.backend!='cuda' and (a.require_cache or a.compile_cache or a.ptxas_level is not None or a.artifact_kind):raise ValueError('CUDA compiler settings require CUDA backend')
        if a.slang_root:os.environ['NIKKE_SLANG_ROOT']=str(a.slang_root.resolve())
        if a.compile_cache:os.environ['NIKKE_CUDA_COMPILE_CACHE']=str(a.compile_cache.resolve())
        if a.require_cache:os.environ['NIKKE_CUDA_CACHE_REQUIRED']='1'
        if a.ptxas_level is not None:os.environ['NIKKE_CUDA_PTXAS_OPT_LEVEL']=str(a.ptxas_level)
        if a.artifact_kind:os.environ['NIKKE_CUDA_ARTIFACT']=a.artifact_kind
        result=run_capture(a.capture,a.backend,a.timeout,a.original_workspace,a.smoke,a.cpu_only)
    elif a.command=='_child':
        # Generated source copies are captured before comparison, including a mismatch.
        child(a.capture,a.backend,a.smoke,a.compile_only);return
    elif a.command=='audit':result=audit_capture(a.capture)
    elif a.command=='status':result=dict(run=load(a.capture/'run.json'),result=load(a.capture/'result.json') if (a.capture/'result.json').exists() else None)
    elif a.command=='collect':result=collect(a.capture,a.out)
    elif a.command=='export':result=export_results(a.capture,a.out)
    elif a.command=='import':result=import_results(a.archive,a.dest)
    else:
        # Historical fixed reports remain supported by their existing sealers.
        runpy.run_path(str(ROOT/f'research/seal-world-v{a.version}-cuda.py'),run_name='__main__');return
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.command=='compile' or result.get('mode')=='compile-only':
        if not result.get('compiler_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is False:raise SystemExit(2)
        return
    if a.command in ('run','audit','replay'):
        if result.get('cpu_verified') or result.get('smoke_verified'):return
        if not result.get('calculation_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is False:raise SystemExit(2)


if __name__=='__main__':main()
