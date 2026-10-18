"""Persist v23 only after fixed-source integration and catalog evidence passes."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def save(path,data):(ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def text(path):
    b=(ROOT/path).read_bytes();return b.decode('utf-16' if b.startswith(b'\xff\xfe') else 'utf-8-sig')
def rows(path):return [json.loads(line) for line in text(path).splitlines() if line.startswith('{')]
normal=read('research/detail-normal-acceptance.json');ptx=read('research/detail-immunity-ptx-verification.json')
catalog=read('research/detail-catalog-batch-verification.json');ui=read('research/detail-immunity-ui-verification.json')
api=rows('research/detail-immunity-api-verification.log')[-1]
common=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json',
        'app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
for report in [normal,ptx,catalog,api,ui]:
    assert report['passed'],report.get('scope')
    for f in common:assert report['source_sha256'][f]==hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),f
assert normal['tests_run']==30 and not normal['skipped']
assert len(ptx['cases'])==54 and all(row['passed'] for row in ptx['cases'])
native=[r for r in rows('research/detail-normal-acceptance.log') if 'per_name_per_recipient_used' in r.get('checks',{})]
assert len(native)==54 and all(row['passed'] for row in native)
assert catalog['compiled_characters']==124 and len(catalog['cases'])==248 and not catalog['not_executed']
assert len(set((r['character'],r['backend']) for r in catalog['cases']))==248
assert 'pass 20' in text('research/detail-immunity-node-tests.log') and 'fail 0' in text('research/detail-immunity-node-tests.log')
assert api['compute']['cpu_verification']['matched'] and ui['compute']['cpu_verification']['matched']
for manifest,source,binary,key in [('app/detail_effects-build.json','app/detail_effects.cu','app/detail_effects.ptx','ptx_sha256'),
                                   ('app/detail_effects-sm86.json','app/detail_effects.cu','app/detail_effects-sm86.cubin','binary_sha256')]:
    data=read(manifest)
    assert data['abi']=='detail_immunity_v23'
    assert data['source_sha256']==hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    assert data[key]==hashlib.sha256((ROOT/binary).read_bytes()).hexdigest()
save('research/detail-immunity-api-verification.json',api)
save('research/detail-immunity-verification.json',dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,
    cpu_trace_used_as_gpu_input=False,cases=native+ptx['cases'],scope=ptx['scope'],source_sha256=ptx['source_sha256']))
coverage=read('research/detail-coverage-immunity.json');audit=read('research/detail-all-effects-audit.json')
for f,digest in audit['compiler_source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest,f
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
    feature='v23 debuff immunity and independent-squad CUDA block execution',abi='detail_immunity_v23',
    workspace_bytes_per_squad=api['compute']['workspace_bytes'],compiled_characters=coverage['supported'],
    catalog_characters=coverage['characters'],favorite_contexts_compiled=audit['accepted_contexts'],favorite_contexts_total=audit['total_contexts'],
    compilation_is_not_all_context_parity=True,current_catalog_verified=True,catalog_cases=248,catalog_scope=catalog['scope'],
    python_focused_tests_passed=30,python_focused_seconds=normal['seconds'],node_tests_passed=20,
    immunity_cases=108,raw_immunity_cases=16,normal_api_total=api['total'],normal_ui_total=ui['total'],
    reports=['research/detail-immunity-verification.json','research/detail-catalog-batch-verification.json',
             'research/detail-normal-acceptance.json','research/detail-immunity-api-verification.json','research/detail-immunity-ui-verification.json'],
    fixes=['Retain the enemy sentinel when application filtering uses an ally-only ordered notification list.',
           'Use one independent CUDA block per autonomous squad; heterogeneous same-warp batches reproduced an execution fault on SM86.'],
    remaining=['79 default characters and 327 favorite contexts still rejected; compilation is not all-situation parity.',
               'No all-character/all-effect completion claim; incoming boss HP/cover/parts/projectiles and other effects remain.',
               'Charge-speed immunity has twelve CPU reference cases but is not yet ported to GPU.',
               'No new full-suite regression claim; the focused suite has 30 tests.'],
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in common+[
        'scripts/verify-immunity-detail.py','scripts/verify-catalog-batch-detail.py','scripts/verify-normal-detail.py',
        'tests/test_detail_immunity.py','tests/test_detail_batch.py','app/gpu_service.py','server.mjs','web/app.js','web/index.html']})
assert report['workspace_bytes_per_squad']==306072
save('research/detail-immunity-checkpoint.json',report)
progress=read('research/detail-expansion-next.json');progress['generated_at']=report['generated_at'];progress['objective_complete']=False
progress['previous_checkpoint_path']='research/detail-shields-checkpoint.json';progress['checkpoint']={**report,'path':'research/detail-immunity-checkpoint.json'}
progress['layout']['workspace_bytes']=report['workspace_bytes_per_squad'];progress.pop('current_work',None)
progress['next_cpu_reference']='research/detail-charge-immunity-cpu-references.json';save('research/detail-expansion-next.json',progress)
print(json.dumps({k:report[k] for k in ['passed','objective_complete','compiled_characters','favorite_contexts_compiled','catalog_cases','immunity_cases','python_focused_tests_passed']}))
