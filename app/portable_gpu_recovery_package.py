"""Controller-only migration of one audited pre-device failure; no retry edits."""
import ast,copy,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path
from portable_continuation_package import owner_snapshot,source_guard

SCHEMA='controller-gpu-recovery-v1'
REPLACED=('scripts/nikke_gpu.py','scripts/run-gpu-packet.py','app/portable_staged_preflight.py')
ADDED=('app/portable_gpu_recovery_package.py','app/portable_gpu_recovery.py',
       'app/portable_staged_origin.py','app/portable_staged_failure.py','tests/test_portable_gpu_recovery.py')


def patch_cli(text):
    tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    main.name='_pre_recovery_main'
    # Preserve every old function, global registry and the complete original
    # main body. Dispatch only the reviewed recovery command before forwarding.
    wrapper=ast.parse('''
def main(argv=None):
    from portable_gpu_recovery import dispatch
    return dispatch(SimpleNamespace(**globals()),_pre_recovery_main,argv)
''').body[0]
    index=tree.body.index(main);tree.body.insert(index+1,wrapper)
    return ast.unparse(ast.fix_missing_locations(tree))+'\n'


def patch_flow(text):
    tree=ast.parse(text)
    context=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='context')
    group=next(n for n in context.body if isinstance(n,ast.If) and ast.unparse(n.test)=="'resume_parent' in c")
    replacement=ast.parse('''
if 'recovery_parent' in c:
    expected_groups=[]
elif 'resume_parent' in c:
    pass
''').body[0]
    replacement.orelse=[group];context.body[context.body.index(group)]=replacement
    insertion=ast.parse('''
if m.get('controller_gpu_recovery') and 'recovery_parent' not in c:
    raise ValueError('Recovery capsule requires its bound recovery transaction')
''').body[0]
    # Insert after the existing identity/host check, before group planning.
    context.body.insert(context.body.index(replacement),insertion)
    admit=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admit')
    check=next(n for n in admit.body if isinstance(n,ast.If) and ast.unparse(n.test)=='actual != m')
    insert=ast.parse('''
if 'recovery_parent' in c:
    from portable_gpu_recovery import admit_context
    return admit_context(cli,m,c)
''').body[0]
    admit.body.insert(admit.body.index(check)+1,insert)
    return ast.unparse(ast.fix_missing_locations(tree))+'\n'


def guarded_sources(old,new):
    if new['scripts/nikke_gpu.py']!=patch_cli(old['scripts/nikke_gpu.py']):raise ValueError('Recovery changed original CLI outside its dispatcher')
    if new['app/portable_staged_preflight.py']!=patch_flow(old['app/portable_staged_preflight.py']):raise ValueError('Recovery changed original preflight outside its bridge')
    # Existing audit guards also prove all nine input/claim/finish functions
    # and the fresh native loop retain their exact AST, including decorators.
    original=copy.deepcopy(old);patched=copy.deepcopy(new)
    a=ast.parse(original['scripts/nikke_gpu.py']);b=ast.parse(patched['scripts/nikke_gpu.py'])
    for n in b.body:
        if isinstance(n,ast.FunctionDef) and n.name=='_pre_recovery_main':n.name='main'
    # source_guard deliberately ignores main; the exact patch equality above
    # already protects both the old main and the new dispatcher.
    b.body=[n for n in b.body if not (isinstance(n,ast.FunctionDef) and n.name=='main' and any(isinstance(x,ast.ImportFrom) and x.module=='portable_gpu_recovery' for x in n.body))]
    patched['scripts/nikke_gpu.py']=ast.unparse(b)
    source_guard(original,patched)


def projection(original,names):
    metadata=copy.deepcopy(original)
    if metadata is None:return None
    omitted=metadata['omitted'];names=set(names)
    if set(omitted)&names:raise ValueError('Recovery payload collides with original omissions')
    metadata.update(retained_files=len(names),original_files=len(names)+len(omitted),
        original_names_sha256=hashlib.sha256(json.dumps(sorted(names|set(omitted)),separators=(',',':')).encode()).hexdigest())
    return metadata


def validate_lineage(cli,current,base_root):
    base_root=Path(base_root).resolve();original=cli.load(base_root/'gpu-package.json');meta=current.get('controller_gpu_recovery',{})
    if (meta.get('schema')!=SCHEMA or meta.get('base_package_id')!=original.get('package_id')
        or meta.get('base_manifest_sha256')!=cli.sha((base_root/'gpu-package.json').read_bytes())
        or original.get('controller_gpu_recovery') or current['suite']!=original['suite']
        or current['golden']!=original['golden'] or current.get('purpose')!=original.get('purpose') or current.get('purpose')!='sealed'):
        raise ValueError('Recovery source/golden owner mismatch')
    old={r['path']:r for r in original['files']};new={r['path']:r for r in current['files']}
    if set(old)&set(ADDED) or set(new)!=set(old)|set(ADDED):raise ValueError('Recovery payload changed its reviewed file set')
    if any(new[n]!=r for n,r in old.items() if n not in REPLACED):raise ValueError('Recovery changed original calculation/data/test bytes')
    if current.get('payload_projection')!=projection(original.get('payload_projection'),new):raise ValueError('Recovery changed the original payload projection')
    guarded_sources({n:(base_root/n).read_text() for n in REPLACED},{n:(cli.ROOT/n).read_text() for n in REPLACED})
    return original


def make(cli,base,auditor,output):
    from portable_staged_preflight import outside
    base=Path(base).resolve();auditor=Path(auditor).resolve();output=outside(output,[base,auditor])
    if output.exists():raise FileExistsError(output)
    info=owner_snapshot(cli,base);original=info['manifest'];inspector=owner_snapshot(cli,auditor)['manifest']
    if original.get('purpose')!='sealed' or original.get('controller_gpu_recovery'):raise ValueError('Only one audited-failure migration is supported')
    if not any(r['path']=='app/portable_staged_origin.py' for r in inspector['files']):raise ValueError('Origin auditor does not contain the complete preflight audit')
    payload={r['path']:(base/r['path']).read_bytes() for r in original['files']}
    if set(ADDED)&set(payload):raise ValueError('Recovery helpers already exist in original owner')
    old={n:payload[n].decode() for n in REPLACED}
    payload['scripts/nikke_gpu.py']=patch_cli(old['scripts/nikke_gpu.py']).encode()
    payload['app/portable_staged_preflight.py']=patch_flow(old['app/portable_staged_preflight.py']).encode()
    payload['scripts/run-gpu-packet.py']=(cli.ROOT/'scripts/run-gpu-packet.py').read_bytes()
    for name in ADDED:payload[name]=(cli.ROOT/name).read_bytes()
    guarded_sources(old,{n:payload[n].decode() for n in REPLACED})
    with tempfile.TemporaryDirectory(prefix='nikke-gpu-recovery-') as tmp:
        root=Path(tmp)
        for name,raw in payload.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        m=copy.deepcopy(original);m.pop('package_id')
        m['files']=cli.file_records(root,payload)
        if 'payload_projection' in m:m['payload_projection']=projection(m['payload_projection'],payload)
        m['controller_gpu_recovery']=dict(schema=SCHEMA,base_package_id=original['package_id'],
            base_manifest_sha256=cli.sha((base/'gpu-package.json').read_bytes()),
            auditor_package_id=inspector['package_id'],auditor_manifest_sha256=cli.sha((auditor/'gpu-package.json').read_bytes()),
            replaced=list(REPLACED),added=list(ADDED))
        m['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=cli.ROOT,text=True).strip()
        m['working_tree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=cli.ROOT,text=True).strip())
        m['package_id']=cli.package_id(m)
        # Recheck every original byte before publishing a completed archive.
        if owner_snapshot(cli,base)!=info:raise ValueError('Original owner changed during recovery packaging')
        cli.check_records(auditor,inspector['files'])
        with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('gpu-package.json',json.dumps(m,indent=2))
            for name,raw in payload.items():z.writestr(name,raw)
    return dict(package_id=m['package_id'],base_package_id=original['package_id'],auditor_package_id=inspector['package_id'],
        files=len(payload),archive_bytes=output.stat().st_size,archive_sha256=cli.sha(output.read_bytes()),gpu_calls=0,calculation_verified=False)
