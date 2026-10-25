"""Test-only refresh of an unclaimed, failed-preflight development packet.

Copy frozen math/input/oracle code, never the workspace's newer implementation.
The normal full native preflight and independent audit remain mandatory.
"""
import argparse,ast,copy,hashlib,importlib.util,json,os,re,tempfile,zipfile
from pathlib import Path

OLD_LAUNCHER="if __name__=='__main__':main()"
LAUNCHER="""if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='refresh-tests':
        from portable_test_repackage import main as refresh_tests_main
        refresh_tests_main(ROOT,sys.argv[2:])
    else:main()
"""
def digest(raw):return hashlib.sha256(raw).hexdigest()
def core(raw):
    tree=ast.parse(raw)
    allowed={ast.dump(ast.parse(x).body[0],include_attributes=False) for x in (OLD_LAUNCHER,LAUNCHER)}
    if not tree.body or ast.dump(tree.body[-1],include_attributes=False) not in allowed:raise ValueError('Unreviewed CLI launcher')
    return ast.dump(ast.Module(body=tree.body[:-1],type_ignores=[]),include_attributes=False)

def unclaimed(source,capture,package_id):
    run=json.loads((capture/'run.json').read_text())
    if run.get('package_id')!=package_id or run.get('mode')!='gpu' or run.get('status')!='failed':raise ValueError('Matching failed preflight capture required')
    if list(source.glob('gpu-claimed-*.json')) or any((capture/name).exists() for name in ('start.json','execution.json','evidence.json','readback.bin')):raise ValueError('Consumed execution claim or started GPU run cannot be refreshed')

def refresh(api,source,capture,workspace,tests,output):
    source=Path(source).resolve();capture=Path(capture).resolve();workspace=Path(workspace).resolve();output=Path(output).absolute()
    if output.exists() or output.is_symlink():raise FileExistsError(output)
    if not tests or len(set(tests))!=len(tests):raise ValueError('Unique explicit test replacements required')
    for name in tests:
        if not re.fullmatch(r'tests/test_[A-Za-z0-9_]+\.py',name):raise ValueError('Only existing test Python files may be replaced')
    manifest_raw=(source/'gpu-package.json').read_bytes();m=json.loads(manifest_raw)
    if m['schema']!=api.SCHEMA or m['package_id']!=api.package_id(m) or m.get('purpose')!='development' or m.get('selected_cases'):raise ValueError('Unfiltered development packet required')
    unclaimed(source,capture,m['package_id']);api.check_records(source,m['files'])
    artifacts_raw=(capture/'artifacts.json').read_bytes();artifacts=json.loads(artifacts_raw);api.check_records(capture,artifacts['files'])
    rows={r['path']:r for r in m['files']}
    if len(rows)!=len(m['files']) or not set(tests)<=rows.keys():raise ValueError('Replacement must already belong to the frozen payload')
    replacements={};updates=[]
    for name,row in rows.items():
        api.safe_name(name);path=workspace/name
        if not path.is_file() or path.is_symlink():raise ValueError('Workspace payload missing or linked: '+name)
        raw=path.read_bytes()
        if name in tests:
            ast.parse(raw)
            if digest(raw)!=row['sha256']:replacements[name]=raw;updates.append(dict(path=name,before_sha256=row['sha256'],after_sha256=digest(raw)))
        elif digest(raw)!=row['sha256']:
            if name!='scripts/nikke_gpu.py' or core(raw)!=core((source/name).read_bytes()):raise ValueError('Non-test workspace source changed: '+name)
    if not updates:raise ValueError('No test content changes')
    verified=api.verify_saved_package(source)
    if verified!=m:raise ValueError('Source package changed during verification')
    new=copy.deepcopy(m)
    for row in new['files']:
        if row['path'] in replacements:row.update(bytes=len(replacements[row['path']]),sha256=digest(replacements[row['path']]))
    new['working_tree_dirty']=True
    new['test_refresh']=dict(source_package_id=m['package_id'],preflight_capture=str(capture),preflight_artifacts_sha256=digest(artifacts_raw),tests=updates)
    new['package_id']=api.package_id(new)
    partial=None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent,prefix='.'+output.name+'.',suffix='.partial',delete=False) as stream:
            partial=Path(stream.name)
            with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('gpu-package.json',json.dumps(new,ensure_ascii=False,indent=2))
                for row in new['files']:archive.writestr(row['path'],replacements.get(row['path'],(source/row['path']).read_bytes()))
            stream.flush();os.fsync(stream.fileno())
        with zipfile.ZipFile(partial) as archive:
            if len(archive.namelist())!=len(new['files'])+1 or json.loads(archive.read('gpu-package.json'))!=new:raise ValueError('Refreshed archive inventory changed')
            for row in new['files']:
                raw=archive.read(row['path'])
                if len(raw)!=row['bytes'] or digest(raw)!=row['sha256']:raise ValueError('Refreshed archive bytes changed')
        unclaimed(source,capture,m['package_id']);api.check_records(source,m['files']);api.check_records(capture,artifacts['files'])
        if (source/'gpu-package.json').read_bytes()!=manifest_raw or (capture/'artifacts.json').read_bytes()!=artifacts_raw:raise ValueError('Source/capture anchor changed')
        os.link(partial,output)
    finally:
        if partial is not None:partial.unlink(missing_ok=True)
    return dict(passed=True,package_id=new['package_id'],source_package_id=m['package_id'],tests=updates,files=len(new['files']),bytes=output.stat().st_size,archive_sha256=digest(output.read_bytes()),
        frozen_non_test_payload_preserved=True,golden_unchanged=True,gpu_calls=0,native_battle_calls=0,calculation_verified=False,
        scope='Only test bytes changed; source packet/capture preserved; full native preflight and GPU execution still required')

def main(workspace,argv):
    parser=argparse.ArgumentParser(prog='nikke_gpu.py refresh-tests')
    for name in ('source-package','source-capture','out'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--test',action='append',required=True);args=parser.parse_args(argv)
    spec=importlib.util.spec_from_file_location('test_refresh_cli',Path(workspace)/'scripts/nikke_gpu.py');api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    with api.forbid_gpu():result=refresh(api,args.source_package,args.source_capture,workspace,args.test,args.out)
    print(json.dumps(result,ensure_ascii=False,indent=2))
