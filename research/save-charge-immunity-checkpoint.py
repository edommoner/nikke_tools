"""Save v24 only when current-source battle, catalog, API and UI gates pass."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def save(path,data):(ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def text(path):
    b=(ROOT/path).read_bytes();return b.decode('utf-16' if b.startswith(b'\xff\xfe') else 'utf-8-sig')
normal=read('research/detail-normal-acceptance.json');main=read('research/detail-charge-immunity-verification.json')
catalog=read('research/detail-catalog-charge-immunity-verification.json');ui=read('research/detail-charge-immunity-ui-verification.json')
api=[json.loads(line) for line in text('research/detail-charge-immunity-api-verification.log').splitlines() if line.startswith('{')][-1]
common=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json',
        'app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
for report in [normal,main,catalog,api,ui]:
    assert report['passed'],report.get('scope')
    for f in common:assert report['source_sha256'][f]==hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),f
assert normal['tests_run']==32 and not normal['skipped']
assert len(main['cases'])==156 and all(row['passed'] for row in main['cases'])
raw=[row for row in main['cases'] if row['all_real_skills_retained']]
assert len(raw)==24 and all(row['checks']['real_core_condition_exercised'] and row['checks']['real_immunity_and_exempt_equipment_exercised'] for row in raw)
assert catalog['compiled_characters']==125 and len(catalog['cases'])==250 and not catalog['not_executed']
assert len(set((row['character'],row['backend']) for row in catalog['cases']))==250
assert api['core_modes_separate'] and api['compute']['cpu_verification']['matched'] and ui['compute']['cpu_verification']['matched']
assert 'pass 20' in text('research/detail-charge-immunity-node-tests.log') and 'fail 0' in text('research/detail-charge-immunity-node-tests.log')
for manifest,binary,key in [('app/detail_effects-build.json','app/detail_effects.ptx','ptx_sha256'),('app/detail_effects-sm86.json','app/detail_effects-sm86.cubin','binary_sha256')]:
    data=read(manifest);assert data['abi']=='detail_charge_immunity_v24'
    assert data['source_sha256']==hashlib.sha256((ROOT/'app/detail_effects.cu').read_bytes()).hexdigest()
    assert data[key]==hashlib.sha256((ROOT/binary).read_bytes()).hexdigest()
audit=read('research/detail-all-effects-audit.json');coverage=read('research/detail-coverage-charge-immunity.json')
for f,digest in audit['compiler_source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest,f
save('research/detail-charge-immunity-api-verification.json',api)
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
    feature='v24 signed charge-speed immunity, source-group rounding, overflow conversion and static core predicate',
    abi='detail_charge_immunity_v24',workspace_bytes_per_squad=api['compute']['workspace_bytes'],
    compiled_characters=coverage['supported'],catalog_characters=coverage['characters'],
    favorite_contexts_compiled=audit['accepted_contexts'],favorite_contexts_total=audit['total_contexts'],
    compilation_is_not_all_context_parity=True,current_catalog_verified=True,catalog_cases=250,catalog_scope=catalog['scope'],
    charge_cases=156,raw_liberalio_cases=24,core_boundary_inputs=[0,.999,1,50],
    python_focused_tests_passed=32,python_focused_seconds=normal['seconds'],node_tests_passed=20,
    normal_api_total=api['total'],normal_api_core_cache_separate=True,normal_ui_total=ui['total'],
    reports=['research/detail-charge-immunity-verification.json','research/detail-catalog-charge-immunity-verification.json',
             'research/detail-normal-acceptance.json','research/detail-charge-immunity-api-verification.json','research/detail-charge-immunity-ui-verification.json'],
    remaining=['78 default characters and 323 favorite contexts remain rejected.',
               'Red Hood still rejects pierce_range; coefficient tests are not full raw Red Hood support.',
               'Core presence is immutable input in this static-boss model; live phase changes and parts are not covered.',
               'Full range geometry, incoming damage/cover/down/revive, healing storage, accumulation and other source constructs remain.',
               'No full-suite or all-character/all-effect completion claim; focused suite has32 tests.'],
    next_cpu_reference='research/detail-range-geometry-cpu-references.json',
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in common+[
        'scripts/verify-charge-immunity-detail.py','scripts/audit-charge-immunity.py','scripts/verify-normal-detail.py',
        'tests/test_detail_charge_immunity.py','scripts/smoke-detail.mjs','app/gpu_service.py','server.mjs','web/app.js','web/index.html']})
assert report['workspace_bytes_per_squad']==306072
save('research/detail-charge-immunity-checkpoint.json',report)
progress=read('research/detail-expansion-next.json');progress['generated_at']=report['generated_at'];progress['objective_complete']=False
progress['previous_checkpoint_path']='research/detail-immunity-checkpoint.json';progress['checkpoint']={**report,'path':'research/detail-charge-immunity-checkpoint.json'}
progress.pop('current_work',None);progress['next_cpu_reference']=report['next_cpu_reference']
progress['next_implementation']=['Live range/part/projectile geometry, hit selection and destruction; range1288 CPU primitive references are groundwork only',
    'Incoming HP/cover/decoy damage, received-damage splitting, down/revive and live boss phases',
    'Remaining authored control grammar, named/team hit contexts, skill copy and damage accumulation',
    'Outgoing healing/storage and upstream omitted Healing/Assister cubes',
    'Remaining condition/target/scaling grammar, capacity bounds and lazy-target history across slot reuse',
    'Every rejected character/favorite context, varied real squads and comprehensive regression verification']
save('research/detail-expansion-next.json',progress)
print(json.dumps({key:report[key] for key in ['passed','objective_complete','compiled_characters','favorite_contexts_compiled','catalog_cases','charge_cases','python_focused_tests_passed']}))
