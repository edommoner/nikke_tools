"""Close v35 production evidence without claiming the all-effects goal done."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
archive=ROOT/'research/ports/v35-hp-edge-staged-verified';manifest=json.loads((archive/'archive-manifest.json').read_text(encoding='utf-8'))
for p,h in manifest['files'].items():
    source=(archive/p).resolve();assert source.is_relative_to(archive)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==h,p
for backend in ('native','ptx'):
    r=json.loads((archive/f'research/detail-hp-edge-separated-{backend}.json').read_text(encoding='utf-8'))
    assert r['passed'] and len(r['cases'])==39 and not r['not_run_cases'] and not r['cpu_trace_used_as_gpu_input']
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json'):
    assert sha('app/'+name)==hashlib.sha256((archive/'research/staging/v35/app'/name).read_bytes()).hexdigest(),name
reports=['research/detail-normal-acceptance.json','research/detail-hp-edge-api-verification.json','research/detail-hp-edge-browser-verification.json'];sources=set()
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'],path
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),path;sources.update(r['source_sha256'])
    if path.endswith('normal-acceptance.json'):assert r['tests_run']==95 and r['skipped']==0
    if '-api-' in path:assert r['pure_gpu_path_verified'] and r['compute']['cpu_verification']['matched'] and r['compute']['workspace_bytes']==1074184
    if '-browser-' in path:assert r['browser_interaction_verified']
coverage=json.loads((ROOT/'research/detail-hp-edge-coverage.json').read_text(encoding='utf-8'));inventory=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
assert coverage['supported']==150 and coverage['characters']==203 and inventory['accepted_contexts']==589 and inventory['total_contexts']==812
for r,field in ((coverage,'source_sha256'),(inventory,'compiler_source_sha256')):
    assert all(sha(p)==h for p,h in r[field].items());sources.update(r[field])
lost_path='research/detail-lost-hp-cpu-reference.json';lost=json.loads((ROOT/lost_path).read_text(encoding='utf-8'))
assert lost['cpu_reference_verified'] and not lost['gpu_implemented'] and len(lost['cases'])==8
assert all(sha(p)==h for p,h in lost['source_sha256'].items());sources.update(lost['source_sha256'])
cover_path='research/detail-cover-revival-cpu-reference.json';cover=json.loads((ROOT/cover_path).read_text(encoding='utf-8'))
assert cover['cpu_reference_verified'] and not cover['gpu_implemented'] and len(cover['cases'])==9
assert all(sha(p)==h for p,h in cover['source_sha256'].items());sources.update(cover['source_sha256']);sources.add(cover_path)
sources.update(['README.md','research/boss-gpu-integration-notes.json','research/save-hp-edge-checkpoint.py','research/finalize-hp-edge-docs.py','research/detail-hp-edge-coverage.json','research/detail-all-effects-audit.json',lost_path,'research/ports/v35-hp-edge-staged-verified/archive-manifest.json','scripts/build-combat.py','scripts/build-detail-native.py'])
api=json.loads((ROOT/'research/detail-hp-edge-api-verification.json').read_text(encoding='utf-8'))
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,abi='detail_hp_edge_v35',workspace_bytes_per_squad=1074184,
    feature='GPU-owned synchronous HP threshold crossing/exact count, squad/adjacent HP events and adjacent maximum transitions; ordered recipients, nested-heal guard, separate self/named event namespaces and revival edge suppression.',
    cases_per_backend=39,authored_cases=24,namespace_cases=3,actual_skill_squad_cases=12,backends=['native','ptx'],normal_tests_passed=95,normal_tests_skipped=0,pre_CUDA_boundary_tests=5,
    compiled_characters=150,catalog_characters=203,favorite_contexts_compiled=589,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,
    ordinary_API_and_browser_verified=True,pure_gpu_path_verified=True,fictional_owned_data=True,live_account_import_verified=False,speedup_claim=False,
    ordinary_total=api['total'],ordinary_original_total=api['original_total'],ordinary_delta=api['delta'],damage_assumed_monotonic=False,
    staging_archive=str(archive.relative_to(ROOT)).replace('\\','/'),rejected_namespace_archive='research/ports/v35-before-self-event-namespace-fix',reports=reports,
    next_dependency=dict(report=lost_path,cpu_reference_cases=8,gpu_implemented=False),
    next_cover_dependency=dict(report=cover_path,cpu_reference_cases=9,gpu_implemented=False),
    remaining=['53 default characters and 223 favorite contexts still reject. Accepted compilation is not all-character/all-combination battle parity.','Dynamic lost-HP scaling, cover revival/controls and random broken-cover targets, healing overcharge storage, enemy debuffs/DOT, geometry and upstream omissions remain.','CPU equality is against the pinned engine and explicit revival bridge; it does not establish every in-game mechanic or live import success.'],
    source_sha256={p:sha(p) for p in sorted(sources)},report_sha256={p:sha(p) for p in reports})
(ROOT/'research/detail-hp-edge-checkpoint.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';j=json.loads(p.read_text(encoding='utf-8'));j.update(generated_at=r['generated_at'],objective_complete=False,checkpoint=r,current_work=None,next_survival_dependency=r['next_dependency'],next_cover_dependency=r['next_cover_dependency'])
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,abi=r['abi'],objective_complete=False,normal_tests=95)))
