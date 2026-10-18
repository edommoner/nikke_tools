"""Save v26 only from current-source whole-battle, lifecycle, API and UI evidence."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def current(r):
 for f,h in r['source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
formal=read('research/detail-live-parts-verification.json');assert formal['passed'];current(formal)
assert len(formal['cases'])==88
for backend in ('native','ptx'):
 rows=[r for r in formal['cases'] if r['backend']==backend];assert len(rows)==44 and all(r['passed'] for r in rows)
 assert sorted(r['count'] for r in rows if r['kind']!='battle')==[108,512]
 battles=[r for r in rows if r['kind']=='battle'];assert len(battles)==42 and sum(r['raw_skills_retained'] for r in battles)==20
 assert all(r['checks']['parts_state_equal'] and r['checks']['final_random_state'] for r in battles)
catalog=read('research/detail-catalog-live-parts-verification.json');assert catalog['passed'];current(catalog)
assert catalog['compiled_characters']==132 and len(catalog['cases'])==264 and not catalog['not_executed']
assert all(r['checks']['final_random_state'] for r in catalog['cases'])
listeners=read('research/detail-part-destroy-listeners-verification.json');assert listeners['passed'] and len(listeners['cases'])==20;current(listeners)
assert all(r['raw_skills_retained'] and r['checks']['raw_events_exercised'] and r['checks']['parts_state_equal'] and r['checks']['final_random_state'] for r in listeners['cases'])
normal=read('research/detail-normal-acceptance.json');assert normal['passed'] and normal['tests_run']==41 and normal['skipped']==0;current(normal)
api=read('research/detail-live-parts-api-verification.json');assert api['passed'];current(api)
assert all(api[k] for k in ('normal_compare_gpu','board_gpu','unsupported_cpu_fallback','cache_separated','shooting_modes_separate','gauge_modes_separate','seed_cache_separated','core_modes_separate','parts_cache_separate'))
assert api['compute']['cpu_verification']['parts_state_equal'] and any(p['destroyed'] for p in api['parts_state'])
ui=read('research/detail-live-parts-ui-verification.json');assert ui['passed'];current(ui)
assert ui['backend']=='cuda_detail' and all(ui['cpu_verification'].values()) and ui['cpu_verification']['parts_state_equal']
assert ui['scope_parts_separate'] and ui['preset_parts_restored'] and len(ui['parts_state'])==2
assert ui['parts_state'][0]['damage']>0 and not ui['parts_state'][0]['destroyed'] and ui['parts_state'][1]['destroyed']
audit=read('research/detail-all-effects-audit.json');assert audit['accepted_contexts']==517 and audit['total_contexts']==812
for f,h in audit['compiler_source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
node=(ROOT/'research/detail-live-parts-node-tests.log').read_bytes();node=node.decode('utf-16' if node.startswith(b'\xff\xfe') else 'utf-8-sig');assert 'pass 22' in node and 'fail 0' in node
files=['app/detail_gpu.py','app/detail_world.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json',
 'app/engine_worker.py','app/engine_compat.py','app/gpu_service.py','scripts/build-combat.py','scripts/build-detail-native.py','scripts/verify-live-parts-detail.py','scripts/verify-normal-detail.py','scripts/smoke-detail.mjs',
 'tests/test_detail_world.py','scripts/verify-part-destroy-listeners.py','web/app.js','web/parts-model.mjs','web/roster-model.mjs','web/index.html','web/style.css','server.mjs']
hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
for f in ('app/detail_effects-build.json','app/detail_effects-sm86.json'):
 m=read(f);assert m['abi']=='detail_live_parts_v26' and m['source_sha256']==hashes['app/detail_effects.cu']
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
 feature='v26 authored fixed live reach parts, pierce/explosion range, per-target overkill/destruction, next-frame notifications, lifesteal and normal UI',
 abi='detail_live_parts_v26',workspace_bytes_per_squad=320816,compiled_characters=132,catalog_characters=203,favorite_contexts_compiled=517,favorite_contexts_total=812,
 compilation_is_not_all_context_parity=True,reach_cases_per_backend=512,lifecycle_cases_per_backend=108,whole_battle_cases=84,raw_character_cases=40,catalog_cases=264,
 python_focused_tests_passed=41,python_focused_seconds=normal['seconds'],native_boundary_battles=5,destroy_listener_battles=20,node_tests_passed=22,normal_api_total=api['total'],normal_ui_total=ui['total'],
 source_sha256=hashes,new_characters=['아니스 : 스타','베스티','베스티 : 택티컬 업','도로시 : 세렌디피티','레드 후드'],
 reports=['research/detail-live-parts-verification.json','research/detail-part-destroy-listeners-verification.json','research/detail-catalog-live-parts-verification.json','research/detail-normal-acceptance.json','research/detail-live-parts-api-verification.json','research/detail-live-parts-ui-verification.json'],
 remaining=['71 default characters and 295 favorite contexts remain rejected.','Coordinate area geometry, interruptions/aiming, spawns/reappearance, penalty parts and moving boss state remain unimplemented.',
 'Incoming damage/cover/down/revive, healing storage, accumulation and other source constructs remain.','Only authored fixed non-penalty parts, with selected owned conditions verified; not all characters, favorite variants or combinations.'])
(ROOT/'research/detail-live-parts-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress=read('research/detail-expansion-next.json');progress.update(generated_at=checkpoint['generated_at'],objective_complete=False,previous_checkpoint=progress['checkpoint'],checkpoint=checkpoint,current_work=None,
 next_cpu_reference='research/detail-live-reach-cpu-references.json',range_geometry_cpu_reference='research/detail-range-geometry-cpu-references.json')
(ROOT/'research/detail-expansion-next.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:checkpoint[k] for k in ['passed','objective_complete','compiled_characters','whole_battle_cases','catalog_cases','normal_ui_total']}))
