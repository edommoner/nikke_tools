"""Controller-only capsule: preserve every original calculation/data/test byte."""
import ast,copy,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path

REPLACED=('scripts/nikke_gpu.py','scripts/run-gpu-packet.py','app/portable_staged_preflight.py')
ADDED=('app/portable_continuation_package.py','app/portable_staged_continuation.py','tests/test_portable_staged_continuation.py')
SCHEMA='controller-continuation-v1'


def owner_snapshot(cli,root):
    root=Path(root).resolve();m=cli.load(root/'gpu-package.json')
    if m.get('schema')!=cli.SCHEMA or m.get('package_id')!=cli.package_id(m):raise ValueError('Original package identity changed')
    cli.check_records(root,m['files'])
    before=cli.file_records(root,['gpu-package.json',*REPLACED])
    script="""import importlib.util,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);s=importlib.util.spec_from_file_location('continuation_original_owner',root/'scripts/nikke_gpu.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c);m=c.verify_package(root)
print(json.dumps(dict(manifest=m,config=c.SUITES[m['suite']],smoke=c.SMOKE_TESTS)))
"""
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    r=subprocess.run([sys.executable,'-B','-c',script,str(root)],cwd=root,env=env,capture_output=True,text=True,check=True,timeout=60)
    info=json.loads(r.stdout)
    if info['manifest']!=m or cli.file_records(root,['gpu-package.json',*REPLACED])!=before:
        raise ValueError('Original owner changed during inspection')
    return info


def functions(text):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}


def source_guard(old,new):
    a=functions(old['scripts/nikke_gpu.py']);b=functions(new['scripts/nikke_gpu.py'])
    if any(b.get(n)!=value for n,value in a.items() if n!='main'):
        raise ValueError('Continuation changed existing CLI calculation/audit functions')
    a=functions(old['app/portable_staged_preflight.py']);b=functions(new['app/portable_staged_preflight.py'])
    for name in ('host','outside','static_input','exclusive','terminal_cpu_stage','prepare_gpu_input','claim_execution','read_gpu_input','finish_gpu'):
        if a.get(name)!=b.get(name):raise ValueError('Continuation changed prepared input or transport: '+name)
    def native_loop(text):
        group=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='group')
        loops=[n for n in ast.walk(group) if isinstance(n,ast.For) and ast.unparse(n.iter)=="c['case_groups'][index]"]
        if len(loops)!=1:raise ValueError('Original fresh native loop missing')
        return ast.dump(loops[0],include_attributes=False)
    if native_loop(old['app/portable_staged_preflight.py'])!=native_loop(new['app/portable_staged_preflight.py']):
        raise ValueError('Continuation changed native reference loop')


def validate_lineage(cli,current,original,original_root):
    metadata=current.get('controller_continuation',{})
    if (metadata.get('schema')!=SCHEMA or metadata.get('base_package_id')!=original['package_id']
        or metadata.get('base_manifest_sha256')!=cli.sha((original_root/'gpu-package.json').read_bytes())
        or current['suite']!=original['suite'] or current['golden']!=original['golden']
        or current.get('purpose')!='sealed' or original.get('purpose')!='sealed'):
        raise ValueError('Continuation source owner/golden mismatch')
    a={r['path']:r for r in original['files']};b={r['path']:r for r in current['files']}
    if set(b)!=set(a)|set(ADDED) or set(ADDED)&set(a):raise ValueError('Continuation introduced unrelated files')
    if any(b[n]!=record for n,record in a.items() if n not in REPLACED):
        raise ValueError('Continuation changed original native/GPU/data/test payload')
    source_guard({n:(original_root/n).read_text() for n in REPLACED},{n:(cli.ROOT/n).read_text() for n in REPLACED})


def make(cli,base,output):
    from portable_package_projection import project,roots_for
    base=Path(base).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    info=owner_snapshot(cli,base);original=info['manifest']
    if original.get('purpose')!='sealed' or original.get('controller_continuation'):
        raise ValueError('Initial continuation requires an ordinary sealed source owner')
    if info['config']!=cli.SUITES[original['suite']]:raise ValueError('Continuation changed suite configuration')
    payload={r['path']:(base/r['path']).read_bytes() for r in original['files']}
    if set(ADDED)&set(payload):raise ValueError('Continuation source already has added files')
    for name in (*REPLACED,*ADDED):payload[name]=(cli.ROOT/name).read_bytes()
    source_guard({n:(base/n).read_text() for n in REPLACED},{n:payload[n].decode() for n in REPLACED})
    with tempfile.TemporaryDirectory(prefix='nikke-controller-capsule-') as tmp:
        root=Path(tmp)
        for name,raw in payload.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        selected,projection=project(root,payload,roots_for(info['config'],cli.SMOKE_TESTS),suite_tests={k:v['tests'] for k,v in cli.SUITES.items()})
        if set(selected)!=set(payload):raise ValueError('Continuation projection dropped original evidence/dependencies')
        m=copy.deepcopy(original);m.pop('package_id');m['files']=cli.file_records(root,payload);m['payload_projection']=projection
        m['controller_continuation']=dict(schema=SCHEMA,base_package_id=original['package_id'],base_manifest_sha256=cli.sha((base/'gpu-package.json').read_bytes()),replaced=list(REPLACED),added=list(ADDED))
        m['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=cli.ROOT,text=True).strip()
        m['working_tree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=cli.ROOT,text=True).strip())
        m['package_id']=cli.package_id(m)
        with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('gpu-package.json',json.dumps(m,indent=2))
            for name,raw in payload.items():archive.writestr(name,raw)
    if owner_snapshot(cli,base)!=info:raise ValueError('Original owner changed during capsule creation')
    return dict(package_id=m['package_id'],base_package_id=original['package_id'],files=len(payload),archive_bytes=output.stat().st_size,archive_sha256=cli.sha(output.read_bytes()),gpu_calls=0)
