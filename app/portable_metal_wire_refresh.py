"""Repair one reviewed pre-device Swift admission failure in a NEW packet.

All oracle/input/shader bytes and expected fingerprints stay frozen. This never
removes a claim, repeats a capture, or certifies a calculation. The new packet
still runs normal full native preflight and independent Metal sealing.
"""
import copy,hashlib,json,os,tempfile,zipfile
from pathlib import Path
from portable_wire_layout import LARGE_OUTPUT_WORDS,metal_guard
PATH='scripts/run-metal-probe.swift'
LEDGER='tests/fixtures/portable-coordinate-resident-arc-source-delta.json'
REVIEWED_OLD_SHA='272e3dc37e0a5710e274f5ab64d9d4eaf7b280ab523ac9bbbff3d2b57f406c3b'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def replacement(raw):
    if sha(raw)!=REVIEWED_OLD_SHA:raise ValueError('Unreviewed Swift transport; no automatic repair')
    text=raw.decode();before=metal_guard(LARGE_OUTPUT_WORDS[:-1]);after=metal_guard()
    if text.splitlines().count(before)!=1 or text.count('MTLCreateSystemDefaultDevice()')!=1 or text.index(before)>text.index('MTLCreateSystemDefaultDevice()'):raise ValueError('Reviewed pre-device admission guard changed')
    return text.replace(before,after,1).encode()

def refresh(api,source,capture,output):
    source,capture=map(lambda p:Path(p).resolve(),(source,capture));output=Path(output).absolute()
    if output.exists() or output.is_symlink():raise FileExistsError(output)
    manifest_raw=(source/'gpu-package.json').read_bytes();m=api.verify_saved_package(source)
    if json.loads(manifest_raw)!=m or m.get('purpose')!='development' or m.get('selected_cases') or m['suite']!='coordinate-resident-arc':raise ValueError('Unfiltered resident arc development packet required')
    rows={r['path']:r for r in m['files']}
    if len(rows)!=len(m['files']) or PATH not in rows or LEDGER not in rows:raise ValueError('Unique frozen transport file required')
    run=json.loads((capture/'run.json').read_text());facts=json.loads((capture/'execution.json').read_text());result=json.loads((capture/'result.json').read_text())
    claim_path=source/'gpu-claimed-metal.json';claim=json.loads(claim_path.read_text())
    if (run.get('package_id')!=m['package_id'] or run.get('backend')!='metal' or run.get('mode')!='gpu' or run.get('status')!='finished' or facts.get('final_child_exit_code')!=1 or facts.get('timed_out') or facts.get('cleanup_error') or result.get('calculation_verified') or claim.get('package_id')!=m['package_id'] or Path(claim['capture']).resolve()!=capture):raise ValueError('Matching terminal pre-device failure required')
    stderr=(capture/'stderr.log').read_bytes()
    if b'Invalid wire layout' not in stderr or b'portable_stage=gpu_dispatch' in stderr or any((capture/name).exists() for name in ('readback.bin','evidence.json')):raise ValueError('Device/dispatch evidence or different failure; repair forbidden')
    if (capture/'comparison.json').exists() and json.loads((capture/'comparison.json').read_text())!={'calculation_verified':False,'comparison_error':'Missing readback.bin'}:raise ValueError('Unexpected comparison evidence; repair forbidden')
    artifacts_raw=(capture/'artifacts.json').read_bytes();api.check_records(capture,json.loads(artifacts_raw)['files'])
    raw=(source/PATH).read_bytes();new_bytes=replacement(raw)
    ledger=json.loads((source/LEDGER).read_text())
    if set(ledger)!={'sources','added_sources'} or PATH in ledger['sources']:raise ValueError('Unexpected audit ledger; no automatic repair')
    ledger['sources'][PATH]=dict(baseline=raw.decode(),baseline_sha256=sha(raw),current=new_bytes.decode(),current_sha256=sha(new_bytes))
    replacements={PATH:new_bytes,LEDGER:(json.dumps(ledger,indent=2)+'\n').encode()}
    before_manifest_sha=sha(manifest_raw);claim_sha=sha(claim_path.read_bytes())
    new=copy.deepcopy(m)
    for row in new['files']:
        if row['path'] in replacements:
            data=replacements[row['path']];row.update(bytes=len(data),sha256=sha(data))
    new['host_wire_refresh']=dict(schema='reviewed-metal-admission-refresh-v1',source_package_id=m['package_id'],source_manifest_sha256=before_manifest_sha,source_artifacts_sha256=sha(artifacts_raw),source_claim_sha256=claim_sha,path=PATH,before_sha256=sha(raw),after_sha256=sha(new_bytes),gpu_calls=0,native_battle_calls=0,full_native_preflight_required=True,independent_seal_required=True,scope='The reviewed Swift allowlist gains the registered2064786 width; the audit ledger gains its exact before/after source row. All calculation/input/oracle/test/CLI bytes and golden remain frozen; original consumed claim retained')
    new['working_tree_dirty']=True;new['package_id']=api.package_id(new)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent,prefix='.'+output.name+'.',suffix='.partial',delete=False) as stream:
            temporary=Path(stream.name)
            with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('gpu-package.json',json.dumps(new,ensure_ascii=False,indent=2))
                for row in new['files']:archive.writestr(row['path'],replacements[row['path']] if row['path'] in replacements else (source/row['path']).read_bytes())
            stream.flush();os.fsync(stream.fileno())
        with zipfile.ZipFile(temporary) as archive:
            if len(archive.namelist())!=len(new['files'])+1:raise ValueError('Refreshed archive inventory changed')
            for row in new['files']:
                data=archive.read(row['path'])
                if len(data)!=row['bytes'] or sha(data)!=row['sha256']:raise ValueError('Refreshed archive bytes changed')
        api.check_records(source,m['files']);api.check_records(capture,json.loads(artifacts_raw)['files'])
        if (source/'gpu-package.json').read_bytes()!=manifest_raw or claim_sha!=sha(claim_path.read_bytes()) or (capture/'artifacts.json').read_bytes()!=artifacts_raw:raise ValueError('Source/capture anchors changed')
        os.link(temporary,output)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return dict(passed=True,package_id=new['package_id'],source_package_id=m['package_id'],files=len(new['files']),bytes=output.stat().st_size,archive_sha256=sha(output.read_bytes()),changed_files=[PATH,LEDGER],golden_unchanged=True,all_other_payload_bytes_unchanged=True,original_claim_retained=True,gpu_calls=0,native_battle_calls=0,calculation_verified=False)
