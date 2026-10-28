"""Exact paired resident Slang generation cache; no NVRTC, driver or GPU calls."""
import base64,hashlib,json,os,platform,re,tempfile
from pathlib import Path
from portable_compile_cache import compile_claim
from portable_resident_layout import reflection_plan,verify_cuda_layout_assertions

SCHEMA=1
OPTIONS=['-fp-mode','precise','-line-directive-mode','none','-reflection-json']

def digest(raw):return hashlib.sha256(raw).hexdigest()
def key(identity):return digest(json.dumps(identity,sort_keys=True,separators=(',',':')).encode())
def file_digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def identity(root,compiler_root,source,entry,hashes):
    root=Path(root);compiler_root=Path(compiler_root).resolve();files={}
    # Runtime/prelude/module assets matter; documentation does not affect codegen.
    for folder in ('bin','lib','include','share/slang'):
        for path in sorted((compiler_root/folder).rglob('*')):
            if path.is_symlink() and path.is_dir():raise ValueError('Slang cache cannot fingerprint a linked module directory')
            if path.is_file():files[path.relative_to(compiler_root).as_posix()]=file_digest(path)
    if not files or not any(n in files for n in ('bin/slangc','bin/slangc.exe')):raise ValueError('Slang cache compiler identity absent')
    if any(k.startswith('SLANG_') or k in ('LD_LIBRARY_PATH','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH') for k in os.environ):
        raise ValueError('Slang generation cache cannot fingerprint external compiler environment overrides')
    sensitive=False
    for name in hashes:
        raw=(root/name).read_bytes()
        if digest(raw)!=hashes[name]:raise ValueError('Slang cache source changed before identity')
        for line in re.findall(rb'(?m)^\s*#\s*include\b([^\n]*)',raw):
            if not re.fullmatch(rb'\s*"[^"\n]+"\s*(?://[^\n]*)?',line):raise ValueError('Slang cache requires a complete literal include closure')
            include=re.search(rb'"([^"]+)"',line).group(1).decode()
            dependency=((root/name).parent/include).resolve().relative_to(root.resolve()).as_posix()
            if dependency not in hashes:raise ValueError('Slang cache literal include missing from source closure')
        if re.search(rb'\bimport\s|__DATE__|__TIME__|__TIMESTAMP__',raw):raise ValueError('Slang generation cache cannot fingerprint implicit modules or time macros')
        if b'__FILE__' in raw:sensitive=True
    consumers={n:file_digest(root/n) for n in ('app/portable_slang_generation.py','app/portable_generation_cache.py','app/portable_resident_layout.py','app/portable_scope_snapshot_audit.py')}
    return dict(schema=SCHEMA,kind='paired-resident-slang-generation',source=source,entry=entry,source_sha256=hashes,options=OPTIONS,
                compiler_root=str(compiler_root),compiler_files=files,host=dict(system=platform.system(),machine=platform.machine(),release=platform.release()),consumers=consumers,path_sensitive_root=str(root.resolve()) if sensitive else None)

def validate_pair(paths,entry):
    plan=reflection_plan(paths,entry);verify_cuda_layout_assertions(paths['cuda'],plan)
    if b'actorStateQueryScopeSnapshot_' in paths['cuda'].read_bytes():
        from portable_scope_snapshot_audit import audit
        audit(paths['cuda'].read_bytes(),paths['metal'].read_bytes())
    if b'markEntry_' in paths['cuda'].read_bytes() or b'initializeHPWatches_' in paths['cuda'].read_bytes():
        from portable_scope_snapshot_audit import audit_resident_appends
        audit_resident_appends(paths['cuda'].read_bytes(),paths['metal'].read_bytes())
    return plan

def artifact_paths(paths):
    return {name:path for target,p in paths.items() for name,path in ((target,p),(target+'-reflection',Path(str(p)+'.reflection.json')))}

def read_entry(path,wanted):
    value=json.loads(path.read_bytes())
    if set(value)!= {'schema','identity','key','artifacts'} or value['schema']!=SCHEMA or value['identity']!=wanted or value['key']!=key(wanted):raise ValueError('Slang generation cache identity mismatch')
    if set(value['artifacts'])!={'cuda','metal','cuda-reflection','metal-reflection'}:raise ValueError('Slang generation cache pair incomplete')
    payload={}
    for name,row in value['artifacts'].items():
        raw=base64.b64decode(row['base64'],validate=True)
        if not raw or len(raw)!=row['bytes'] or digest(raw)!=row['sha256']:raise ValueError('Slang generation cache artifact integrity failure')
        payload[name]=raw
    return value,payload

def atomic(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as stream:
        tmp=Path(stream.name);stream.write(raw);stream.flush();os.fsync(stream.fileno())
    try:tmp.replace(path)
    finally:tmp.unlink(missing_ok=True)

def get_or_generate(root,compiler_root,source,entry,hashes,directory,cache,generate,*,required=False):
    root=Path(root);directory=Path(directory);cache=Path(cache)
    if not cache.is_absolute():raise ValueError('Absolute Slang generation cache required')
    compiler_root=Path(compiler_root).resolve()
    if cache.resolve().is_relative_to(compiler_root):raise ValueError('Slang cache must be outside the compiler distribution')
    expected=identity(root,compiler_root,source,entry,hashes);entry_key=key(expected);path=cache/(entry_key+'.json')
    outputs={t:directory/(Path(source).stem+'.'+suffix) for t,suffix in [('cuda','cu'),('metal','metal')]}
    hit=path.exists()
    if not hit and required:raise RuntimeError('Required Slang generation cache miss; compiler forbidden')
    if not hit:
        with compile_claim(path,entry_key,description='Slang generation'):
            hit=path.exists()
            if not hit:
                with tempfile.TemporaryDirectory(prefix='nikke-generation-miss-') as tmp:
                    generated,after_hashes=generate(Path(tmp))
                    if after_hashes!=hashes:raise ValueError('Slang generation source closure changed')
                    validate_pair(generated,entry)
                    if identity(root,compiler_root,source,entry,hashes)!=expected:raise ValueError('Slang generation inputs changed during compilation')
                    artifacts={n:dict(bytes=len(raw),sha256=digest(raw),base64=base64.b64encode(raw).decode()) for n,p in artifact_paths(generated).items() for raw in [p.read_bytes()]}
                value=dict(schema=SCHEMA,identity=expected,key=entry_key,artifacts=artifacts)
                atomic(path,json.dumps(value,sort_keys=True).encode())
    value,payload=read_entry(path,expected)
    # Validate cached code and both reflections before replacing any live output.
    with tempfile.TemporaryDirectory(prefix='nikke-generation-read-') as tmp:
        staged={t:Path(tmp)/(Path(source).stem+'.'+suffix) for t,suffix in [('cuda','cu'),('metal','metal')]}
        for name,p in artifact_paths(staged).items():p.write_bytes(payload[name])
        validate_pair(staged,entry)
        if identity(root,compiler_root,source,entry,hashes)!=expected:raise ValueError('Slang generation inputs changed before publication')
        for name,p in artifact_paths(outputs).items():atomic(p,payload[name])
    receipt=dict(schema=SCHEMA,identity=expected,key=entry_key,hit=hit,compiler_invocations=0 if hit else 2,artifacts={n:{k:v for k,v in row.items() if k!='base64'} for n,row in value['artifacts'].items()})
    atomic(directory/(Path(source).stem+'.generation-cache.json'),(json.dumps(receipt,sort_keys=True)+'\n').encode())
    return outputs,hashes

def audit_receipt(receipt,source_hashes,paths):
    i=receipt['identity']
    if receipt['schema']!=SCHEMA or i['schema']!=SCHEMA or i['kind']!='paired-resident-slang-generation' or receipt['key']!=key(i) or i['source_sha256']!=source_hashes or i['options']!=OPTIONS or type(receipt['hit']) is not bool or receipt['compiler_invocations']!=(0 if receipt['hit'] else 2):raise ValueError('Slang generation receipt mismatch')
    files=artifact_paths(paths)
    if set(receipt['artifacts'])!=set(files):raise ValueError('Slang generation receipt pair incomplete')
    for name,p in files.items():
        raw=p.read_bytes()
        if receipt['artifacts'][name]!=dict(bytes=len(raw),sha256=digest(raw)):raise ValueError('Slang generation receipt artifact mismatch')
    validate_pair(paths,i['entry'])
    return dict(verified=True,cache_hit=receipt['hit'],compiler_invocations=receipt['compiler_invocations'],gpu_calls=0)
