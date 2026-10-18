"""Close production and archived staging evidence without declaring the full goal done."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
archive=ROOT/'research/ports/v34-survival-final-staged-verified'
manifest=json.loads((archive/'archive-manifest.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((archive/p).read_bytes()).hexdigest()==h for p,h in manifest['files'].items())
reports=['research/detail-normal-acceptance.json','research/detail-survival-api-verification.json','research/detail-survival-cpu-compat-verification.json','research/detail-survival-browser-verification.json']
sources=set()
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'],path
    for p,h in r['source_sha256'].items():assert sha(p)==h,(path,p)
    sources.update(r['source_sha256'])
coverage=json.loads((ROOT/'research/detail-survival-coverage.json').read_text(encoding='utf-8'))
audit=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
assert coverage['supported']==149 and coverage['characters']==203
assert audit['accepted_contexts']==585 and audit['total_contexts']==812
sources.update(['README.md','web/index.html','research/save-survival-checkpoint.py','research/detail-survival-coverage.json','research/detail-all-effects-audit.json','research/boss-gpu-integration-notes.json','research/detail-survival-rejected-normal-acceptance.json','research/ports/v34-survival-final-staged-verified/archive-manifest.json'])
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,abi='detail_survival_v34',workspace_bytes_per_squad=1049568,
    feature='Integrated GPU down/revive, passive restoration and persist flags, dead-target selection, action/burst restart, shared counters and existing timers; stat-scoped live healing recipients.',
    compiled_characters=149,catalog_characters=203,favorite_contexts_compiled=585,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,
    native_survival_cases=49,ptx_survival_cases=49,native_burst_stage_cases_in_normal_suite=56,healing_regressions_per_backend=3,native_repeated_lethal_long_cases=4,
    previous_extended_matrix_archive='research/ports/v34-burstfix-staged-verified',previous_matrix_is_before_final_b1_predicate_fix=True,
    python_focused_tests_passed=87,production_cpu_bridge_cases=5,browser_interaction_verified=True,staging_archive='research/ports/v34-survival-final-staged-verified',reports=reports,
    remaining=['54 default characters and 227 favorite contexts still reject; accepted compilation is not all-combination battle parity.','HP-edge triggers, attack-attached debuffs, enemy debuff/dot worlds, cover controls, geometry and other upstream/data omissions remain.','No live-account import or speedup claim. CPU parity is against the explicitly bridged pinned engine, not proof of in-game mechanics.'],
    source_sha256={p:sha(p) for p in sorted(sources)},report_sha256={p:sha(p) for p in reports})
(ROOT/'research/detail-survival-checkpoint.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
path=ROOT/'research/detail-expansion-next.json';journal=json.loads(path.read_text(encoding='utf-8'));journal.update(generated_at=r['generated_at'],objective_complete=False,checkpoint=r,current_work=None)
journal['next_survival_dependency']=dict(report='research/detail-hp-edge-cpu-reference.json',cpu_reference_cases=8,gpu_implemented=False)
path.write_text(json.dumps(journal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,abi=r['abi'],objective_complete=False)))
