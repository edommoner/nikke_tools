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
                       golden='research/portable-world-readiness-v3-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=75,native=60,
                       tests=['test_portable_readiness.py','test_portable_compile_cache.py','test_portable_gpu_cli.py','test_portable_cuda_artifact.py','test_portable_phase_audit.py']),
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

SCHEMA = 1


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


def child(capture, backend, smoke=False):
    deadline = time.monotonic()+60
    while not (capture/'start.json').exists():
        if time.monotonic() >= deadline:
            raise RuntimeError('Containment gate not released; GPU not started')
        time.sleep(.02)
    if smoke:
        write(capture/'smoke.json',dict(pid=os.getpid(),ppid=os.getppid(),gpu_calls=0)); return
    m = verify_package(ROOT)
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
            if receipt['identity']['options']!=cuda_compile_options(kind):
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
                    native=dict(status=64)
                else:native=adapter.compare(block,domain)
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


def seal_development(package_root, capture, output):
    """Explicit GPU0 seal of a successful immutable Metal development capture."""
    # Use the package's own imports and auditors in a fresh process. Its files
    # are verified before native work; never patch a consumed package in place.
    script = """import importlib.util,json,sys,pathlib
root=pathlib.Path(sys.argv[1]);capture=pathlib.Path(sys.argv[2])
s=importlib.util.spec_from_file_location('seal_cli',root/'scripts/nikke_gpu.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=m.verify_package(root)
if not m.is_development(p) or m.load(capture/'run.json')['backend']!='metal':raise ValueError('Metal development capture required')
a=m.audit_capture(capture)
if not a['calculation_verified']:raise ValueError('Failed development capture cannot be sealed')
r=m.compare_readback(p,capture)
g=dict(input_sha256=r['input_sha256'],output_sha256=r['output_sha256'],source_sha256=p['golden']['source_sha256'],entries=r['entries'],generated_normalized=r['generated_normalized'])
print(json.dumps(dict(golden=g,package_id=p['package_id'],audit=a)))
"""
    completed=subprocess.run([sys.executable,'-c',script,str(package_root.resolve()),str(capture.resolve())],
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


def run_job(capture,backend,timeout,original_workspace=None,smoke=False):
    bounded=bounded_module()
    env=os.environ.copy();env.pop('__PYVENV_LAUNCHER__',None)
    env['PYTHONPATH']=os.pathsep.join([*site.getsitepackages(),env.get('PYTHONPATH','')])
    interpreter=getattr(sys,'_base_executable',sys.executable) if os.name=='nt' else sys.executable
    command=[interpreter,str(Path(__file__).resolve()),'_child','--capture',str(capture),'--backend',backend]
    if smoke:command.append('--smoke')
    write(capture/'runtime.json',dict(interpreter=interpreter,parent_interpreter=sys.executable,platform=platform.platform(),slang_root=os.environ.get('NIKKE_SLANG_ROOT'),cuda_artifact_kind=os.environ.get('NIKKE_CUDA_ARTIFACT','cubin') if backend=='cuda' else None,compile_cache_enabled=bool(os.environ.get('NIKKE_CUDA_COMPILE_CACHE')),launcher_variable_removed='__PYVENV_LAUNCHER__' not in env))
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
        pre=cpu_preflight(m);write(capture/'cpu.json',pre)
        test_results=[]
        for pattern in SUITES[m['suite']]['tests']:
            started=time.perf_counter()
            completed=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-p',pattern],cwd=ROOT,capture_output=True,timeout=60)
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


def audit_capture(capture,verify_artifacts=True):
    m=verify_package(ROOT)
    if load(capture/'run.json')['package_id']!=m['package_id']:raise ValueError('Capture belongs to another package')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
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
    if (capture/'observation.json').exists():
        from windows_validation_observer import compare_snapshots
        o=load(capture/'observation.json')
        if 'before' in o and 'after' in o:
            comparison=compare_snapshots(o['before'],o['after'])
            if o.get('comparison')!=comparison:raise ValueError('Process comparison mismatch')
            immediate=0 <= o['after']['observed_unix_ns']-facts['wait_completed_unix_ns'] <= 30_000_000_000
            preservation=bool(immediate and not facts['observation_error'] and comparison['all_monitored_processes_preserved'] and comparison['identified_nikke_service_preservation_verified'])
    containment=True if backend!='cuda' else False
    if backend=='cuda' and (capture/'job.json').exists():
        records=load(capture/'job.json')['records']
        if len(records)==1:
            row=records[0];pre=row['pre_gate'];post=row['post_wait']
            phase_rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()] if (capture/'phases.jsonl').exists() else []
            containment=bool(row['pre_gate_verified'] and not row['inspection_error'] and post
                             and pre['child_pid']==post['child_pid']==row['child_pid']
                             and pre['child_ppid']==post['child_ppid']==row['wrapper_pid']
                             and pre['job_members']==[row['child_pid']] and post['job_members']==[]
                             and pre['child_creation_filetime_ticks']==post['child_creation_filetime_ticks']
                             and verify_cuda_trace(phase_rows,pid=row['child_pid'])
                             and pre['observed_unix_ns']<=phase_rows[0]['wall_time_ns']<=phase_rows[-1]['wall_time_ns']<=post['observed_unix_ns'])
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
    a=sub.add_parser('cache-check');a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('seal');a.add_argument('--package-root',type=Path,required=True);a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('cases');a.add_argument('--suite',choices=SUITES,required=True)
    a=sub.add_parser('inventory');a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('package');a.add_argument('--suite',choices=SUITES,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--develop',action='store_true');a.add_argument('--case',action='append',default=[])
    a=sub.add_parser('unpack');a.add_argument('--archive',type=Path,required=True);a.add_argument('--dest',type=Path,required=True)
    for name in ('run','_child'):
        a=sub.add_parser(name);a.add_argument('--capture',type=Path,required=True);a.add_argument('--backend',choices=('metal','cuda'),required=True);a.add_argument('--smoke',action='store_true')
        if name=='run':
            a.add_argument('--cpu-only',action='store_true');a.add_argument('--timeout',type=int,default=180);a.add_argument('--original-workspace',type=Path);a.add_argument('--slang-root',type=Path)
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
    elif a.command=='cache-check':result=check_compile_cache(a.capture,a.out)
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
    elif a.command=='package':result=make_package(a.suite,a.out,develop=a.develop,cases=a.case)
    elif a.command=='unpack':result=dict(package_id=unpack(a.archive,a.dest))
    elif a.command=='run':
        if a.slang_root:os.environ['NIKKE_SLANG_ROOT']=str(a.slang_root.resolve())
        result=run_capture(a.capture,a.backend,a.timeout,a.original_workspace,a.smoke,a.cpu_only)
    elif a.command=='_child':
        # Generated source copies are captured before comparison, including a mismatch.
        child(a.capture,a.backend,a.smoke);return
    elif a.command=='audit':result=audit_capture(a.capture)
    elif a.command=='status':result=dict(run=load(a.capture/'run.json'),result=load(a.capture/'result.json') if (a.capture/'result.json').exists() else None)
    elif a.command=='collect':result=collect(a.capture,a.out)
    elif a.command=='export':result=export_results(a.capture,a.out)
    elif a.command=='import':result=import_results(a.archive,a.dest)
    else:
        # Historical fixed reports remain supported by their existing sealers.
        runpy.run_path(str(ROOT/f'research/seal-world-v{a.version}-cuda.py'),run_name='__main__');return
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.command in ('run','audit'):
        if result.get('cpu_verified') or result.get('smoke_verified'):return
        if not result.get('calculation_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is False:raise SystemExit(2)


if __name__=='__main__':main()
