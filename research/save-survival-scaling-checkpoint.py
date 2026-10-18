"""Seal production v36 evidence; do not claim all-character/effect completion."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
archive='research/ports/v36-survival-scaling-staged-verified'
manifest=json.loads((ROOT/archive/'archive-manifest.json').read_text(encoding='utf-8'))
assert all(sha(archive+'/'+p)==h for p,h in manifest['files'].items())
reports=['research/detail-normal-acceptance.json','research/detail-survival-scaling-api-verification.json','research/detail-survival-scaling-browser-verification.json']
sources=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'],path
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),path;sources.update(r['source_sha256'])
normal=json.loads((ROOT/reports[0]).read_text(encoding='utf-8'));assert normal['tests_run']==108 and not normal['skipped']
api=json.loads((ROOT/reports[1]).read_text(encoding='utf-8'));assert api['pure_gpu_path_verified'] and api['cpu_verification']
for path,field in [('research/detail-survival-scaling-coverage.json','source_sha256'),('research/detail-all-effects-audit.json','compiler_source_sha256')]:
    inventory=json.loads((ROOT/path).read_text(encoding='utf-8'));assert all(sha(p)==h for p,h in inventory[field].items()),path
    sources.add(path);sources.update(inventory[field])
sources.update(['README.md','research/boss-gpu-integration-notes.json','research/save-survival-scaling-checkpoint.py',archive+'/archive-manifest.json','scripts/build-combat.py','scripts/build-detail-native.py'])
node_log=(ROOT/'research/detail-survival-scaling-node-tests.log').read_text(encoding='utf-8')
assert 'pass 26' in node_log and 'fail 0' in node_log and 'skipped 0' in node_log
sources.add('research/detail-survival-scaling-node-tests.log')
sources.update(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'tests').glob('*.test.mjs'))
sources.update(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'web').glob('*.mjs'))
next_path='research/detail-cover-capacity-cpu-reference.json';reference=json.loads((ROOT/next_path).read_text(encoding='utf-8'))
assert reference['cpu_reference_verified'] and not reference['gpu_implemented'] and len(reference['cases'])==9
assert all(sha(p)==h for p,h in reference['source_sha256'].items());sources.add(next_path);sources.update(reference['source_sha256'])
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,abi='detail_survival_scaling_v36',workspace_bytes_per_squad=1074184,
    feature='GPU-owned dynamic lost-HP buff values, cover revival and random living broken-cover targeting, runtime cover-alive gates; narrow CPU requested-revival query bridge.',
    authored_cases_per_backend=28,actual_skill_squad_cases_per_backend=12,backends=['native','ptx'],PTX_legacy_regression_cases=88,normal_tests_passed=normal['tests_run'],normal_tests_skipped=0,normal_execution=normal.get('execution','single suite'),pre_CUDA_and_CPU_boundary_tests=11,node_tests_passed=26,
    compiled_characters=152,catalog_characters=203,favorite_contexts_compiled=597,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,
    ordinary_API_and_browser_verified=True,pure_gpu_path_verified=True,fictional_owned_data=True,live_account_import_verified=False,speedup_claim=False,
    ordinary_total=api['total'],ordinary_original_total=api['original_total'],ordinary_delta=api['delta'],damage_assumed_monotonic=False,
    staging_archive=archive,reports=reports,next_cover_capacity_dependency=dict(report=next_path,cpu_direct_cases=9,gpu_implemented=False),
    remaining=['51 default characters and 215 favorite contexts still reject; compilation acceptance is not all-combination battle parity.',
      'Bay still rejects received_dmg_split and max_hp scaling. Cover controls, healing overcharge storage, enemy debuffs/DOT, geometry and pinned upstream omissions remain.',
      'CPU parity is against the pinned engine and explicit revival bridges, not proof of every in-game mechanic or live account import.'],
    source_sha256={p:sha(p) for p in sorted(sources)},report_sha256={p:sha(p) for p in reports})
(ROOT/'research/detail-survival-scaling-checkpoint.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';j=json.loads(p.read_text(encoding='utf-8'));j.update(generated_at=r['generated_at'],objective_complete=False,checkpoint=r,current_work=None)
j['next_survival_dependency']=dict(report='research/detail-lost-hp-cpu-reference.json',gpu_implemented=True,production_checkpoint='research/detail-survival-scaling-checkpoint.json')
j['next_cover_dependency']=dict(report='research/detail-cover-revival-cpu-reference.json',gpu_implemented=True,production_checkpoint='research/detail-survival-scaling-checkpoint.json')
j['next_cover_capacity_dependency']=r['next_cover_capacity_dependency']
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,abi=r['abi'],objective_complete=False,normal_tests=r['normal_tests_passed'])))
