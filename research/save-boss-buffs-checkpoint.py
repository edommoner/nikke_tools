"""v32 is a verified step toward all effects, never completion of that goal."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
paths=['research/detail-boss-buffs-verification.json','research/detail-boss-buffs-long-verification.json','research/detail-normal-acceptance.json','research/detail-boss-buffs-api-verification.json','research/detail-boss-buff-boundaries-verification.json']
reports=[]
for p in paths:
 r=json.loads((ROOT/p).read_text(encoding='utf-8-sig'));assert r['passed'],p
 assert r['source_sha256'] and all(sha(f)==h for f,h in r['source_sha256'].items()),'Stale '+p
 reports.append(r)
full,long,normal,api,boundary=reports
assert len(full['cases'])==40 and len(long['cases'])==6
assert len(boundary['cases'])==2 and all(r['checks']['actual_gpu'] and r['checks']['world_frames'] for r in boundary['cases'])
assert normal['tests_run']==77 and normal['skipped']==0
assert all(r['checks']['actual_gpu'] and r['checks']['world_frames'] and r['checks']['final_random_state'] for r in full['cases']+long['cases'])
assert api['patterns_verified'] and api['unsupported_boss_cpu_parity'] and api['compute']['backend']=='cuda_detail'
build=json.loads((ROOT/'app/detail_effects-sm86.json').read_text(encoding='utf-8'))
assert build['abi']=='detail_boss_buffs_v32' and build['source_sha256']==sha('app/detail_effects.cu') and build['binary_sha256']==sha('app/detail_effects-sm86.cubin')
audit=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
assert audit['accepted_contexts']==529 and all(sha(f)==h for f,h in audit['compiler_source_sha256'].items())
coverage=json.loads((ROOT/'research/detail-boss-buffs-coverage.json').read_text(encoding='utf-8'));assert (coverage['supported'],coverage['characters'])==(135,203)
incoming=json.loads((ROOT/'research/detail-incoming-targets-cpu-reference.json').read_text(encoding='utf-8'))
assert incoming['cpu_reference_verified'] and not incoming['gpu_implemented'] and len(incoming['cases'])==19
assert all(sha(f)==h for f,h in incoming['source_sha256'].items())
groundwork=[]
for p,n in [('research/detail-incoming-damage-cpu-reference.json',20),('research/detail-incoming-target-transitions-cpu-reference.json',6)]:
 r=json.loads((ROOT/p).read_text(encoding='utf-8'))
 assert r['cpu_reference_verified'] and not r['gpu_implemented'] and len(r['cases'])==n
 assert all(sha(f)==h for f,h in r['source_sha256'].items())
 groundwork.append(dict(report=p,cpu_reference_cases=n,gpu_implemented=False,sha256=sha(p)))
ui_path='research/detail-boss-buffs-ui-session-verification.json'
ui=json.loads((ROOT/ui_path).read_text(encoding='utf-8'))
assert ui['passed'] and ui['browser_interaction_verified'] is False
assert all(sha(f)==h for f,h in ui['source_sha256'].items())
raw=(ROOT/'research/detail-boss-buffs-node-tests.log').read_bytes();log=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig');assert all(x in log for x in ('tests 26','pass 26','fail 0'))
files=['app/detail_boss.py','app/detail_world.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py','server.mjs','web/app.js','web/index.html','scripts/verify-boss-clock-detail.py','scripts/verify-boss-buffs-detail.py','scripts/verify-normal-detail.py','scripts/smoke-detail-boss-buffs.mjs','scripts/audit-incoming-targets.py','tests/test_detail_boss_buffs.py','research/detail-enemy-cleanse-characters.json','research/detail-boss-buffs-coverage.json','research/detail-all-effects-audit.json','research/detail-incoming-targets-cpu-reference.json','research/boss-gpu-integration-notes.json','research/save-boss-buffs-checkpoint.py','README.md']
c=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,abi=build['abi'],feature='Ordered boss defense/received-damage buffs, real boss caster identity, deferred enemy buff cleanse, lifecycle-preserving dispel and read-only end-of-frame CPU observation',workspace_bytes_per_squad=api['compute']['workspace_bytes'],compiled_characters=135,catalog_characters=203,favorite_contexts_compiled=529,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,boss_buff_cases=len(full["cases"]),long_native_180_second_battles=len(long["cases"]),python_focused_tests_passed=normal["tests_run"],node_tests_passed=26,normal_api_total=api['total'],incoming_cpu_reference_cases=19,incoming_gpu_implemented=False,raw_enemy_cleanse_character_audit=full['raw_enemy_cleanse_character_audit'],reports=paths,source_sha256={p:sha(p) for p in files},report_sha256={p:sha(p) for p in paths},remaining=['68 default characters and 283 favorite contexts remain rejected. Rosanna is still blocked by stealth.','Incoming attack/targeting, cover/down/revive, damage split, outgoing healing/storage, boss interrupt/summon/shield/vanish/debuff, coordinate geometry and upstream omissions remain.','The CPU target audit is groundwork only; it is not a GPU implementation. All-character/all-combination correctness and a speedup are unproven.'])
c.update(boundary_cases=len(boundary['cases']),incoming_additional_cpu_groundwork=groundwork,ui_saved_session_validation=dict(report=ui_path,sha256=sha(ui_path),browser_interaction_verified=False))
(ROOT/'research/detail-boss-buffs-checkpoint.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'))
if r['checkpoint']['abi']!=c['abi']:r['previous_checkpoint']=r['checkpoint']
r.update(checkpoint=c,current_work=None,objective_complete=False,generated_at=c['generated_at']);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:c[k] for k in ('passed','abi','objective_complete','boss_buff_cases','python_focused_tests_passed','normal_api_total')}))
