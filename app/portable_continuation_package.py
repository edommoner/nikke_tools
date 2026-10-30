"""Preserve calculation bytes; optional reviewed controls retain their originals."""
from portable_product_programs import configuration as product_configuration
import ast,copy,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path

REPLACED=('scripts/nikke_gpu.py','scripts/run-gpu-packet.py','app/portable_staged_preflight.py')
ADDED=('app/portable_continuation_package.py','app/portable_staged_continuation.py','tests/test_portable_staged_continuation.py')
SCHEMA='controller-continuation-v1'
FULL_SCHEMA='controller-continuation-full-owner-v1'
FULL_REPLACED=(*REPLACED,'app/portable_continuation_package.py','app/portable_staged_continuation.py')
FULL_ADDED=('tests/test_portable_staged_tail_budget.py',)
REPAIRED_SCHEMA='controller-continuation-reviewed-controls-v1'
REPAIR_LEDGER='tests/fixtures/portable-control-fixture-repairs-v1.json'
REPAIR_LEDGER_SHA='30920e25cea3db9be660809d8d061723e252a138a97d06273a858cd70de2a734'
REPAIR_CHANGED=('app/portable_coordinate_resident_arc_source_contract.py','tests/test_portable_generation_separation.py','tests/test_required_metal_cache_preflight.py')
REPAIR_ADDED=('app/portable_generation_extraction_source_contract.py','tests/fixtures/portable-generation-append-audit-delta.json')
REPAIR_TEST='tests/test_portable_continuation_repairs.py'
REPAIR_ORIGINALS={'research/control-repair-originals/'+name:name for name in REPAIR_CHANGED}


def repair_manifest(root,original):
    """An explicit fixed repair set, never arbitrary test/source replacement."""
    import hashlib
    root=Path(root);raw=(root/REPAIR_LEDGER).read_bytes()
    digest=lambda b:hashlib.sha256(b).hexdigest()
    if digest(raw)!=REPAIR_LEDGER_SHA:raise ValueError('Unreviewed control repair ledger')
    r=json.loads(raw);old={row['path']:row for row in original['files']}
    if (r.get('schema')!='reviewed-control-fixture-repairs-v1' or r['base_package_id']!=original['package_id']
        or set(r['changed'])!=set(REPAIR_CHANGED) or set(r['added'])!=set(REPAIR_ADDED)):
        raise ValueError('Control repair owner or exact file set changed')
    for name,row in r['changed'].items():
        before=old.get(name,{})
        if {k:before.get(k) for k in ('bytes','sha256')}!=row['before']:raise ValueError('Control repair original bytes changed: '+name)
    for name in r['added']:
        if name in old:raise ValueError('Control repair addition already exists')
    for name,expected in {**{n:v['after'] for n,v in r['changed'].items()},**r['added']}.items():
        b=(root/name).read_bytes()
        if dict(bytes=len(b),sha256=digest(b))!=expected:raise ValueError('Control repair bytes changed: '+name)
    expected='tests/fixtures/portable-generation-extraction.json'
    if (old.get(expected,{}).get('sha256')!=r['original_extraction_expected_sha256']
        or digest((root/expected).read_bytes())!=r['original_extraction_expected_sha256']):
        raise ValueError('Original extraction expectations changed')
    return r


def layout(original,*,repair_controls=False):
    names={r['path'] for r in original['files']}
    present=names&set(ADDED)
    if not present:
        if repair_controls:raise ValueError('Reviewed controls require a full ordinary owner')
        return SCHEMA,REPLACED,ADDED
    if present!=set(ADDED) or not set(FULL_REPLACED)<=names or set(FULL_ADDED)&names:
        raise ValueError('Incomplete or already extended continuation controller')
    if 'payload_projection' in original:raise ValueError('Full continuation owner must retain an unprojected payload')
    if repair_controls:
        added=(*FULL_ADDED,*REPAIR_ADDED,REPAIR_LEDGER,REPAIR_TEST,*REPAIR_ORIGINALS)
        if set(added)&names:raise ValueError('Control repairs already present in original owner')
        return REPAIRED_SCHEMA,(*FULL_REPLACED,*REPAIR_CHANGED),added
    return FULL_SCHEMA,FULL_REPLACED,FULL_ADDED


def owner_snapshot(cli,root):
    root=Path(root).resolve();m=cli.load(root/'gpu-package.json')
    if m.get('schema')!=cli.SCHEMA or m.get('package_id')!=cli.package_id(m):raise ValueError('Original package identity changed')
    cli.check_records(root,m['files'])
    before=cli.file_records(root,['gpu-package.json',*REPLACED])
    script="""import importlib.util,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);s=importlib.util.spec_from_file_location('continuation_original_owner',root/'scripts/nikke_gpu.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c);m=c.verify_package(root)
print(json.dumps(dict(manifest=m,config=(c.suite_config(m) if hasattr(c,'suite_config') else c.SUITES[m['suite']]),smoke=c.SMOKE_TESTS)))
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
    repaired=metadata.get('schema')==REPAIRED_SCHEMA
    schema,replaced,added=layout(original,repair_controls=repaired)
    if (metadata.get('schema')!=schema or metadata.get('base_package_id')!=original['package_id']
        or metadata.get('base_manifest_sha256')!=cli.sha((original_root/'gpu-package.json').read_bytes())
        or current['suite']!=original['suite'] or current['golden']!=original['golden']
        or current.get('purpose')!='sealed' or original.get('purpose')!='sealed'):
        raise ValueError('Continuation source owner/golden mismatch')
    a={r['path']:r for r in original['files']};b={r['path']:r for r in current['files']}
    if set(b)!=set(a)|set(added) or set(added)&set(a):raise ValueError('Continuation introduced unrelated files')
    if schema in (FULL_SCHEMA,REPAIRED_SCHEMA) and (metadata.get('replaced')!=list(replaced) or metadata.get('added')!=list(added) or 'payload_projection' in current):
        raise ValueError('Full continuation controller inventory changed')
    if repaired:
        if metadata.get('control_repairs_ledger_sha256')!=REPAIR_LEDGER_SHA:raise ValueError('Control repair manifest anchor changed')
        repairs=repair_manifest(cli.ROOT,original)
        for name,expected in {**{n:r['after'] for n,r in repairs['changed'].items()},**repairs['added']}.items():
            if {k:b[name].get(k) for k in ('bytes','sha256')}!=expected:raise ValueError('Control repair artifact record changed')
        for backup,name in REPAIR_ORIGINALS.items():
            if (cli.ROOT/backup).read_bytes()!=(original_root/name).read_bytes():raise ValueError('Original control repair evidence changed')
    if any(b[n]!=record for n,record in a.items() if n not in replaced):
        raise ValueError('Continuation changed original native/GPU/data/test payload')
    source_guard({n:(original_root/n).read_text() for n in REPLACED},{n:(cli.ROOT/n).read_text() for n in REPLACED})


def make(cli,base,output,*,repair_controls=False):
    from portable_package_projection import project,roots_for
    base=Path(base).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    info=owner_snapshot(cli,base);original=info['manifest']
    if original.get('purpose')!='sealed' or original.get('controller_continuation'):
        raise ValueError('Initial continuation requires an ordinary sealed source owner')
    if info['config']!=product_configuration(cli.SUITES,original):raise ValueError('Continuation changed suite configuration')
    payload={r['path']:(base/r['path']).read_bytes() for r in original['files']}
    schema,replaced,added=layout(original,repair_controls=repair_controls)
    if repair_controls:repair_manifest(cli.ROOT,original)
    for name in (*replaced,*added):payload[name]=((base/REPAIR_ORIGINALS[name]) if name in REPAIR_ORIGINALS else (cli.ROOT/name)).read_bytes()
    source_guard({n:(base/n).read_text() for n in REPLACED},{n:payload[n].decode() for n in REPLACED})
    with tempfile.TemporaryDirectory(prefix='nikke-controller-capsule-') as tmp:
        root=Path(tmp)
        for name,raw in payload.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        m=copy.deepcopy(original);m.pop('package_id');m['files']=cli.file_records(root,payload)
        if schema==SCHEMA:
            selected,projection=project(root,payload,roots_for(info['config'],cli.SMOKE_TESTS),suite_tests={k:v['tests'] for k,v in cli.SUITES.items()})
            if set(selected)!=set(payload):raise ValueError('Continuation projection dropped original evidence/dependencies')
            m['payload_projection']=projection
        m['controller_continuation']=dict(schema=schema,base_package_id=original['package_id'],base_manifest_sha256=cli.sha((base/'gpu-package.json').read_bytes()),replaced=list(replaced),added=list(added))
        if repair_controls:m['controller_continuation']['control_repairs_ledger_sha256']=REPAIR_LEDGER_SHA
        m['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=cli.ROOT,text=True).strip()
        m['working_tree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=cli.ROOT,text=True).strip())
        m['package_id']=cli.package_id(m)
        with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('gpu-package.json',json.dumps(m,indent=2))
            for name,raw in payload.items():archive.writestr(name,raw)
    if owner_snapshot(cli,base)!=info:raise ValueError('Original owner changed during capsule creation')
    return dict(package_id=m['package_id'],base_package_id=original['package_id'],files=len(payload),archive_bytes=output.stat().st_size,archive_sha256=cli.sha(output.read_bytes()),gpu_calls=0)
