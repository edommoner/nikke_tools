"""Save v25 only after inspecting current-source battle, API and UI evidence."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def current(report):
    for f,h in report['source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
formal=read('research/detail-optimal-range-verification.json');assert formal['passed'];current(formal)
assert len(formal['cases'])==62
for backend in ('native','ptx'):
    cases=[r for r in formal['cases'] if r['backend']==backend]
    assert len(cases)==31 and all(r['passed'] for r in cases)
    assert [r['count'] for r in cases if r['kind']=='primitives']==[672]
    raw=[r for r in cases if r.get('raw_skills_retained')]
    assert len(raw)==8 and all(r['checks']['range_decision_changed'] for r in raw)
catalog=read('research/detail-catalog-optimal-range-verification.json');assert catalog['passed'];current(catalog)
assert catalog['compiled_characters']==127 and len(catalog['cases'])==254 and not catalog['not_executed']
assert all(r['checks']['final_random_state'] for r in catalog['cases'])
normal=read('research/detail-normal-acceptance.json');assert normal['passed'];current(normal)
assert normal['tests_run']==36 and normal['skipped']==0
api=read('research/detail-optimal-range-api-verification.json');assert api['passed'];current(api)
assert all(api[k] for k in ('normal_compare_gpu','board_gpu','unsupported_cpu_fallback','cache_separated','shooting_modes_separate','gauge_modes_separate','seed_cache_separated','core_modes_separate'))
ui=read('research/detail-optimal-range-ui-verification.json');assert ui['passed'];current(ui)
assert ui['backend']=='cuda_detail' and all(ui['cpu_verification'].values())
audit=read('research/detail-all-effects-audit.json');assert audit['accepted_contexts']==497 and audit['total_contexts']==812
for f,h in audit['compiler_source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
reach=read('research/detail-live-reach-cpu-references.json');assert reach['passed'] and not reach['gpu_implemented'] and len(reach['cases'])==198;current(reach)
node=(ROOT/'research/detail-optimal-range-node-tests.log').read_bytes();node=node.decode('utf-16' if node.startswith(b'\xff\xfe') else 'utf-8-sig')
assert 'pass 20' in node and 'fail 0' in node
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json',
       'app/engine_worker.py','app/gpu_service.py','scripts/verify-optimal-range-detail.py','scripts/verify-normal-detail.py','tests/test_detail_optimal_range.py','scripts/make-optimal-range-fixture.py','web/app.js','web/index.html']
hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
for f in ('app/detail_effects-build.json','app/detail_effects-sm86.json'):
    manifest=read(f);assert manifest['abi']=='detail_optimal_range_v25' and manifest['source_sha256']==hashes['app/detail_effects.cu']
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
    feature='v25 dynamic optimal distance: live min/max range buffs, outgoing normal damage, innate-weapon activation predicate',
    abi='detail_optimal_range_v25',workspace_bytes_per_squad=306152,compiled_characters=127,catalog_characters=203,
    favorite_contexts_compiled=497,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,
    primitive_cases_per_backend=672,whole_battle_cases=60,raw_character_cases=16,catalog_cases=254,
    python_focused_tests_passed=36,python_focused_seconds=normal['seconds'],node_tests_passed=20,
    normal_api_total=api['total'],normal_ui_total=ui['total'],source_sha256=hashes,
    reports=['research/detail-optimal-range-verification.json','research/detail-catalog-optimal-range-verification.json','research/detail-normal-acceptance.json','research/detail-optimal-range-api-verification.json','research/detail-optimal-range-ui-verification.json'],
    remaining=['76 default characters and 315 favorite contexts remain rejected.',
        'Pierce/explosion range, live parts, coordinate target selection and destruction remain unimplemented.',
        'Incoming damage/cover/down/revive, healing storage, accumulation and other source constructs remain.',
        'Static enemy and selected owned fixtures only; not all characters/effects/favorites/combinations verified.'])
(ROOT/'research/detail-optimal-range-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress=read('research/detail-expansion-next.json');progress.update(generated_at=checkpoint['generated_at'],objective_complete=False,
    previous_checkpoint=progress['checkpoint'],checkpoint=checkpoint,current_work=None,
    next_cpu_reference='research/detail-live-reach-cpu-references.json',range_geometry_cpu_reference='research/detail-range-geometry-cpu-references.json')
(ROOT/'research/detail-expansion-next.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:checkpoint[k] for k in ['passed','objective_complete','compiled_characters','whole_battle_cases','catalog_cases','normal_ui_total']}))
