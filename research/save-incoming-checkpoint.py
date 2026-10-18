"""Publish v33 only after full evidence. This never completes the all-effects goal."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
paths=['research/detail-incoming-native-verification.json','research/detail-incoming-ptx-verification.json','research/detail-incoming-long-verification.json','research/detail-incoming-lifecycle-verification.json','research/detail-normal-acceptance.json','research/detail-incoming-api-verification.json','research/detail-incoming-ui-session-verification.json']
reports=[]
for p in paths:
 r=read(p);assert r['passed'],p
 assert r['source_sha256'] and all(sha(f)==h for f,h in r['source_sha256'].items()),'stale '+p
 reports.append(r)
native,ptx,long,life,normal,api,ui=reports
for r,n in [(native,80),(ptx,80),(long,4),(life,4)]:
 assert len(r['cases'])==n and r['not_run_cases']==0
 assert all(c['passed'] and all(c['checks'].values()) and c['checks']['actual_gpu'] and c['checks']['incoming_frames'] and c['checks']['boss_rng'] and c['checks']['skill_rng'] for c in r['cases'])
assert sum(c['raw_skills_retained'] for c in native['cases'])==22
assert normal['tests_run']==86 and normal['skipped']==0
assert api['incoming_hits_verified'] and api['incoming_hits'] and api['normal_compare_gpu'] and api['board_gpu'] and api['cache_separated'] and api['unsupported_boss_cpu_parity']
assert api['compute']['backend']=='cuda_detail' and api['compute']['cpu_verification']['matched'] and api['compute']['cpu_verification']['incoming_hits_equal']
assert ui['browser_interaction_verified'] is False
build=read('app/detail_effects-sm86.json')
assert build['abi']=='detail_incoming_v33' and build['source_sha256']==sha('app/detail_effects.cu') and build['binary_sha256']==sha('app/detail_effects-sm86.cubin')
audit=read('research/detail-all-effects-audit.json');assert audit['accepted_contexts']==569 and audit['total_contexts']==812 and all(sha(f)==h for f,h in audit['compiler_source_sha256'].items())
coverage=read('research/detail-incoming-coverage.json');assert (coverage['supported'],coverage['characters'])==(145,203)
down=read('research/detail-down-revive-cpu-reference.json');assert down['cpu_reference_verified'] and not down['gpu_implemented'] and len(down['cases'])==8 and all(sha(f)==h for f,h in down['source_sha256'].items())
additional_cpu=[]
for p,n in [('research/detail-down-continuations-cpu-reference.json',6),('research/detail-down-weapon-modes-cpu-reference.json',4)]:
 r=read(p);assert r['cpu_reference_verified'] and not r['gpu_implemented'] and len(r['cases'])==n and all(sha(f)==h for f,h in r['source_sha256'].items())
 additional_cpu.append(dict(report=p,cases=n,gpu_implemented=False,sha256=sha(p)))
files=['app/detail_gpu.py','app/detail_boss.py','app/detail_world.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/engine_compat.py','app/gpu_service.py','server.mjs','web/app.js','web/index.html','web/phase-model.mjs','scripts/verify-incoming-detail.py','scripts/verify-incoming-lifecycle.py','scripts/smoke-detail-incoming.mjs','scripts/verify-incoming-ui-session.mjs','scripts/verify-normal-detail.py','tests/test_detail_incoming.py','scripts/audit-down-revive.py','research/detail-incoming-coverage.json','research/detail-all-effects-audit.json','research/detail-down-revive-cpu-reference.json','research/detail-incoming-api-fixture.json','research/detail-incoming-ui-fixture.json','research/save-incoming-checkpoint.py','README.md']
files+=['research/boss-gpu-integration-notes.json','scripts/audit-down-continuations.py','scripts/audit-down-weapon-modes.py','research/detail-down-continuations-cpu-reference.json','research/detail-down-weapon-modes-cpu-reference.json']
c=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,abi=build['abi'],feature='Integrated GPU incoming attack scheduling, independent boss RNG, live stealth/taunt, shield/cover/decoy/HP layers, invincibility/undying and shared damage; eager dynamic cover repair recipients',workspace_bytes_per_squad=api['compute']['workspace_bytes'],compiled_characters=145,catalog_characters=203,favorite_contexts_compiled=569,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,native_cases=80,ptx_cases=80,long_180_second_raw_squads=4,lifecycle_cases=4,python_focused_tests_passed=86,normal_api_total=api['total'],browser_interaction_verified_this_phase=False,down_revive_cpu_reference_cases=18,down_revive_gpu_implemented=False,first_failure_archive='research/ports/v33-before-cover-ranking-fix',remaining=['58 default characters and 243 favorite contexts are still rejected; compilation acceptance is not all-combination battle parity.','True lethal down/revive, attack-attached debuffs, enemy debuff/dot worlds, cover controls, coordinate geometry, other special effects and upstream model/data omissions remain.','No live account import or speedup claim; CPU parity is scoped to the pinned engine, not independent proof of in-game mechanics.'],reports=paths,additional_cpu_groundwork=additional_cpu,source_sha256={p:sha(p) for p in files},report_sha256={p:sha(p) for p in paths})
c['numeric_comparison']={'integer_damage_and_burst_timeline':'exact','incoming_hit_quantities':'exact after rounding to six decimal places','frame_hp_and_cover_state':{'relative_tolerance':1e-12,'absolute_tolerance':1e-6}}
(ROOT/'research/detail-incoming-checkpoint.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';r=read(str(p.relative_to(ROOT)))
if r['checkpoint']['abi']!=c['abi']:r['previous_checkpoint']=r['checkpoint']
r.update(checkpoint=c,current_work=None,objective_complete=False,generated_at=c['generated_at']);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:c[k] for k in ('passed','abi','objective_complete','native_cases','ptx_cases','python_focused_tests_passed')}))
