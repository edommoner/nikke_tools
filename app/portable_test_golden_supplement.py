"""Add one missing test golden from a sealed packet, preserving all old bytes.

Only expected fingerprints are retained. A normal fresh CPU preflight and
independent seal remain mandatory; no native values, device claims or results
are transferred. The old producer/controller is copied without modification.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def configured_golden(source, suite):
    code="""import importlib.util,json,pathlib,sys
p=pathlib.Path('scripts/nikke_gpu.py')
s=importlib.util.spec_from_file_location('frozen_test_registry',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
print(json.dumps(m.SUITES[sys.argv[1]]['golden']))
"""
    result=subprocess.run([sys.executable,'-c',code,suite],cwd=source,
                          capture_output=True,text=True,check=True,timeout=60)
    return json.loads(result.stdout)


def unclaimed(source):
    if list(source.glob('gpu-claimed-*.json')):
        raise ValueError('A consumed execution claim cannot be supplemented')


def supplement(api,source,capture,donor,suite,output):
    source,capture,donor=map(lambda p:Path(p).resolve(),(source,capture,donor))
    output=Path(output).absolute();receipt=Path(str(output)+'.receipt.json')
    if output.exists() or receipt.exists():raise FileExistsError(output)
    m=api.verify_saved_package(source);d=api.verify_saved_package(donor)
    if m.get('purpose')!='development' or m.get('selected_cases') or d.get('purpose','sealed')!='sealed' or suite==m['suite']:
        raise ValueError('Unfiltered development source and a different sealed test baseline required')
    unclaimed(source)
    result=api.load(capture/'result.json')
    if result.get('schema')!='unit-check-v1' or result.get('package_id')!=m['package_id'] or result.get('passed') is not False or type(result.get('gpu_calls')) is not int or result['gpu_calls']!=0:
        raise ValueError('Matching failed CPU unit capture required')
    api.check_records(capture,api.load(capture/'artifacts.json')['files'])
    capture_anchor=api.sha((capture/'artifacts.json').read_bytes())
    name=configured_golden(source,suite);api.safe_name(name)
    if not name.startswith('research/portable-') or not name.endswith('-expected.json'):
        raise ValueError('Only a registered test golden JSON may be added')
    existing={r['path'] for r in m['files']};records={r['path']:r for r in d['files']}
    if name in existing or (source/name).exists() or name not in records:
        raise ValueError('Golden must be missing in source and owned by sealed donor')
    raw=(donor/name).read_bytes();row=records[name]
    if len(raw)>2*1024*1024 or len(raw)!=row['bytes'] or api.sha(raw)!=row['sha256']:
        raise ValueError('Donor test golden bytes differ or exceed bounded size')
    golden=json.loads(raw)
    if not isinstance(golden,dict) or not isinstance(golden.get('entries'),list) or not isinstance(golden.get('source_sha256'),dict):
        raise ValueError('Expected source-bound test golden schema')
    new=copy.deepcopy(m);new['files'].append(copy.deepcopy(row));new['files'].sort(key=lambda r:r['path'])
    new['working_tree_dirty']=True;new['package_id']=api.package_id(new)
    before={p:api.sha((p/'gpu-package.json').read_bytes()) for p in (source,donor)}
    partial=None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent,delete=False) as stream:
            partial=Path(stream.name)
            with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('gpu-package.json',json.dumps(new,ensure_ascii=False,indent=2))
                for item in new['files']:
                    archive.writestr(item['path'],raw if item['path']==name else (source/item['path']).read_bytes())
            stream.flush();os.fsync(stream.fileno())
        with zipfile.ZipFile(partial) as archive:
            if len(archive.namelist())!=len(new['files'])+1:raise ValueError('Supplemented inventory differs')
            for item in new['files']:
                content=archive.read(item['path'])
                if len(content)!=item['bytes'] or api.sha(content)!=item['sha256']:raise ValueError('Supplemented payload differs')
        unclaimed(source)
        api.check_records(source,m['files']);api.check_records(donor,d['files'])
        api.check_records(capture,api.load(capture/'artifacts.json')['files'])
        if api.sha((capture/'artifacts.json').read_bytes())!=capture_anchor:raise ValueError('Failed unit capture changed')
        if any(api.sha((p/'gpu-package.json').read_bytes())!=digest for p,digest in before.items()):raise ValueError('Source/donor anchors changed')
        os.link(partial,output)
    finally:
        if partial is not None:partial.unlink(missing_ok=True)
    facts=dict(schema='test-golden-supplement-v1',passed=True,package_id=new['package_id'],source_package_id=m['package_id'],donor_package_id=d['package_id'],
        added_file=row,archive_sha256=api.sha(output.read_bytes()),original_file_count=len(m['files']),
        source_manifest_sha256=before[source],donor_manifest_sha256=before[donor],failed_unit_artifacts_sha256=capture_anchor,
        all_existing_payload_bytes_preserved=True,expected_fingerprints_preserved=True,
        fresh_native_preflight_required=True,independent_seal_required=True,gpu_calls=0,native_battle_calls=0,calculation_verified=False)
    api.write(receipt,facts)
    return facts
