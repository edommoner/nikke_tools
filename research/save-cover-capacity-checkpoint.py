"""Seal v37 scope without substituting it for the complete all-effects objective."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
archive='research/ports/v37-cover-capacity-staged-verified';manifest=json.loads((ROOT/archive/'archive-manifest.json').read_text(encoding='utf-8'));assert all(sha(archive+'/'+p)==h for p,h in manifest['files'].items())
reports=['research/detail-cover-capacity-production-verification.json','research/detail-cover-capacity-api-verification.json','research/detail-cover-capacity-browser-verification.json'];sources=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'] and r['abi']=='detail_cover_capacity_v37',path
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),path;sources.update(r['source_sha256'])
focused=json.loads((ROOT/reports[0]).read_text(encoding='utf-8'));assert focused['tests_run']==10 and not focused['skipped'] and focused['whole_squad_cases']==97
api=json.loads((ROOT/reports[1]).read_text(encoding='utf-8'));assert api['pure_gpu_path_verified'] and api['cpu_verification']
for path,field in [('research/detail-cover-capacity-coverage.json','source_sha256'),('research/detail-all-effects-audit.json','compiler_source_sha256')]:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert all(sha(p)==h for p,h in r[field].items());sources.add(path);sources.update(r[field])
next_path='research/detail-decoy-healing-cpu-reference.json';reference=json.loads((ROOT/next_path).read_text(encoding='utf-8'));assert reference['cpu_reference_verified'] and not reference['gpu_implemented'] and len(reference['cases'])==10
assert all(sha(p)==h for p,h in reference['source_sha256'].items());sources.add(next_path);sources.update(reference['source_sha256'])
node=(ROOT/'research/detail-cover-capacity-node-tests.log').read_text(encoding='utf-8');assert 'pass 26' in node and 'fail 0' in node and 'skipped 0' in node
sources.update(['README.md','research/boss-gpu-integration-notes.json','research/save-cover-capacity-checkpoint.py','research/detail-cover-capacity-node-tests.log',archive+'/archive-manifest.json','scripts/build-combat.py','scripts/build-detail-native.py'])
sources.update(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'tests').glob('*.test.mjs'));sources.update(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'web').glob('*.mjs'))
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,abi='detail_cover_capacity_v37',workspace_bytes_per_squad=1074184,feature='GPU-owned original-caster live maximum-HP cover capacity, separate base-percentage and caster-flat contributions, direct value-query semantics without damage bullet override.',
    cases_per_backend=97,authored_cases=15,actual_Tia_squad_cases=6,additional_Moran_A2_cover_cube_cases=2,legacy_regression_cases=74,backends=['native','ptx'],focused_production_tests=10,focused_production_squad_cases=97,boundary_tests=6,production_skipped=0,node_tests_passed=26,full_normal118_rerun=False,
    compiled_characters=153,catalog_characters=203,favorite_contexts_compiled=601,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,ordinary_API_and_browser_verified=True,pure_gpu_path_verified=True,fictional_owned_data=True,live_account_import_verified=False,speedup_claim=False,
    ordinary_total=api['total'],ordinary_original_total=api['original_total'],ordinary_delta=api['delta'],staging_archive=archive,reports=reports,next_decoy_healing_dependency=dict(report=next_path,cpu_direct_cases=10,gpu_implemented=False),
    remaining=['50 default characters and 211 favorite contexts still reject; accepted compilation is not universal battle parity.','Bay received_dmg_split, decoy healing, healing overcharge storage, cover controls, enemy debuffs/DOT, geometry and pinned CPU omissions remain.','Equality is against the pinned CPU and explicit revival bridges; this does not establish every in-game mechanic, a live import, or a speedup.'],
    source_sha256={p:sha(p) for p in sorted(sources)},report_sha256={p:sha(p) for p in reports})
(ROOT/'research/detail-cover-capacity-checkpoint.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';j=json.loads(p.read_text(encoding='utf-8'));j.update(generated_at=r['generated_at'],objective_complete=False,checkpoint=r,current_work=None,next_decoy_healing_dependency=r['next_decoy_healing_dependency'])
j['next_cover_capacity_dependency']=dict(report='research/detail-cover-capacity-cpu-reference.json',gpu_implemented=True,production_checkpoint='research/detail-cover-capacity-checkpoint.json');p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,abi=r['abi'],objective_complete=False,focused_production_tests=10,cases_per_backend=97)))
