"""Publish only source-bound, completed v31 verification; broader migration stays open."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
paths=['research/detail-boss-clock-verification.json','research/detail-boss-clock-long-verification.json','research/detail-normal-acceptance.json','research/detail-boss-clock-api-verification.json','research/detail-boss-clock-ui-verification.json']
reports=[]
for p in paths:
 r=json.loads((ROOT/p).read_text(encoding='utf-8-sig'));assert r['passed'],p
 assert r['source_sha256'] and all(sha(f)==h for f,h in r['source_sha256'].items()),'Stale report: '+p
 assert all(sha(f)==h for f,h in r.get('evidence_sha256',{}).items()),'Stale nested evidence: '+p
 reports.append(r)
full,long,normal,api,ui=reports
assert len(full['cases'])==40 and len(long['cases'])==5
assert normal['tests_run']==70 and not normal['skipped']
assert api['patterns_verified'] and api['unsupported_boss_cpu_parity']
assert ui['backend']=='cuda_detail' and all(ui['cpu_verification'].values())
assert ui['delta_applied'] and ui['boss_events']>0
build=json.loads((ROOT/'app/detail_effects-sm86.json').read_text(encoding='utf-8'))
assert build['abi']=='detail_boss_clock_v31' and build['source_sha256']==sha('app/detail_effects.cu') and build['binary_sha256']==sha('app/detail_effects-sm86.cubin')
audit=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
assert audit['accepted_contexts']==529 and all(sha(f)==h for f,h in audit['compiler_source_sha256'].items())
coverage=json.loads((ROOT/'research/detail-boss-clock-coverage.json').read_text(encoding='utf-8'))
assert (coverage['supported'],coverage['characters'])==(135,203)
raw=(ROOT/'research/detail-boss-clock-node-tests.log').read_bytes();log=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert all(x in log for x in ('tests 26','pass 26','fail 0'))
files=['app/detail_boss.py','app/detail_world.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py','server.mjs','web/app.js','web/index.html','web/style.css','web/phase-model.mjs','web/enemy-model.mjs','web/roster-model.mjs','scripts/verify-boss-clock-detail.py','scripts/verify-normal-detail.py','scripts/smoke-detail-boss-clock.mjs','tests/test_detail_boss_clock.py','tests/phases.test.mjs','research/save-boss-clock-checkpoint.py']
files+=['README.md','research/detail-boss-clock-coverage.json','research/detail-all-effects-audit.json','research/accept-boss-clock-test-repair.py','research/save-boss-clock-ui-evidence.py']
c=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,abi=build['abi'],feature='GPU-owned boss lifecycle, dependency cursors, core/distance/weapon overlays, ordered emissions and normal UI editing',workspace_bytes_per_squad=639072,compiled_characters=135,catalog_characters=203,favorite_contexts_compiled=529,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,boss_cases=40,long_native_180_second_battles=5,python_focused_tests_passed=70,node_tests_passed=26,normal_api_total=api['total'],normal_ui_total=ui['total'],reports=paths,source_sha256={p:sha(p) for p in files},report_sha256={p:sha(p) for p in paths},remaining=['68 default characters and 283 favorite contexts remain rejected.','Boss buff/attack/debuff/interrupt/summon/shield/vanish, target-cleared lifecycle, coordinates and per-part motion remain unsupported.','Incoming damage, cover/down/revive, healing storage, accumulation, omitted upstream effects/cubes and unsupported mixed/periodic/weapon-change team listeners remain.','Finite history and active-slot limits fail closed. These tests do not establish all-character/all-combination correctness or a speedup.'])
(ROOT/'research/detail-boss-clock-checkpoint.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'))
if r['checkpoint']['abi']!=c['abi']:r['previous_checkpoint']=r['checkpoint']
elif r.get('previous_checkpoint',{}).get('abi')==c['abi']:r['previous_checkpoint']=json.loads((ROOT/'research/detail-named-capacity-checkpoint.json').read_text(encoding='utf-8'))
r.update(checkpoint=c,current_work=None,objective_complete=False,generated_at=c['generated_at']);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:c[k] for k in ('passed','abi','objective_complete','boss_cases','python_focused_tests_passed','normal_api_total','normal_ui_total')}))
