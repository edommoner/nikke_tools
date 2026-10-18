"""Save current proof without reducing the all-character/all-effect objective."""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def raw(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
main=read('research/detail-health-reload-verification.json');catalog=read('research/detail-catalog-verification.json');api=read('research/detail-health-reload-api-verification.json')
assert main['passed'] and len(main['cases'])==66
assert catalog['passed'] and catalog['compiled_characters']==103 and len(catalog['cases'])==206
for report in (main,catalog,api):
 assert report['passed']
 for p,h in report['source_sha256'].items():assert sha(p)==h,p
for backend in ('native','ptx'):
 assert sum(c['backend']==backend for c in main['cases'])==33
 assert sum(c['backend']==backend for c in catalog['cases'])==103
for key in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'):assert api[key],key
reg=raw('research/detail-health-reload-tests.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==97 and '\nOK' in reg and 'skipped=' not in reg
node=raw('research/detail-health-reload-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-health-reload.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==103 and audit['accepted_contexts']==400
old=read('research/detail-modes-checkpoint.json')
for p,h in old['source_sha256'].items():
 if p.startswith('research/upstream/'):assert sha(p)==h,p
before=read('research/detail-coverage-modes.json');was={r['character'] for r in before['results'] if r['supported']}
added=[r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in was]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/engine_compat.py','app/gpu_service.py','server.mjs','web/app.js','web/index.html','scripts/verify-detail.py','scripts/verify-health-reload-detail.py','scripts/smoke-detail.mjs','scripts/audit-charge-control.py','tests/test_detail_health_reload.py','research/detail-health-reload-tests.log','research/detail-health-reload-node-tests.log','research/detail-health-reload-api-fixture.json','research/detail-health-reload-ui-fixture.json','research/detail-charge-control-cpu-references.json']
hashes={p:sha(p) for p in files};hashes.update({p:h for p,h in old['source_sha256'].items() if p.startswith('research/upstream/')})
now=datetime.now(timezone.utc).isoformat()
checkpoint={'generated_at':now,'passed':True,'objective_complete':False,'engine_revision':old['engine_revision'],'abi':'detail_health_reload_v13','effect_row_width':256,'compiled_characters':103,'catalog_characters':203,'favorite_contexts_compiled':400,'favorite_contexts_total':812,'compilation_is_not_all_favorite_parity':True,'new_characters':added,'mechanics_cases':66,'primitives_per_backend':12,'synthetic_full_squads_per_backend':13,'new_real_full_squads_per_backend':5,'extra_favorite_and_level_squads_per_backend':3,'catalog_cases':206,'python_tests_passed':97,'python_test_seconds':float(m[2]),'node_tests_passed':20,'normal_api_total':api['total'],'workspace_bytes_per_squad':api['compute']['workspace_bytes'],'cpu_trace_used_as_gpu_input':False,'scope':'Static enemy, expected mode, auto full-charge shooting. Dedicated mechanics, one grown 30-second squad per accepted character on both backends, favorite Exia3/Jill burst level1/7, full regression and normal API verified. Not all characters, favorite contexts, combinations, live enemy state or upstream omissions.','reports':['research/detail-health-reload-verification.json','research/detail-catalog-verification.json','research/detail-health-reload-tests.log','research/detail-health-reload-api-verification.json'],'source_sha256':hashes}
write('research/detail-health-reload-checkpoint.json',checkpoint)
n=read('research/detail-expansion-next.json');n['generated_at']=now;n['objective_complete']=False
n.pop('current_work',None)
n['next_charge_control_reference']={'path':'research/detail-charge-control-cpu-references.json','cases':27,'hold_exercised_cases':14,'scope':'CPU references only; production adapter forces operation.auto=True. Port the input channel, ownership/camera and true hold/release behavior together; do not claim holding from non-firing auto cases.'}
n['checkpoint'].update(compile_coverage=103,previous=98,favorite_contexts_accepted=400,coverage_path='research/detail-coverage-health-reload.json',workspace_abi='detail_health_reload_v13',workspace_bytes_per_squad=checkpoint['workspace_bytes_per_squad'],python_tests_passed=97,python_test_scope=f'97 tests in {m[2]} seconds; no skips',regression_status='passed: Python97, Node20, HP/reload66 native/PTX, accepted-catalog206, normal API HP/delta/equipment GPU/CPU/board/cache/fallback',accepted_catalog_full_squad_cases=206,accepted_catalog_characters=103,catalog_report_current=True,normal_api_demo_gpu_verified=False,normal_api_health_reload_gpu_verified=True,normal_api_health_reload_total=api['total'],health_reload_cases_total=66,health_reload_report='research/detail-health-reload-verification.json',historical_reports_note='Current aggregate: detail-health-reload-checkpoint.json. Earlier dedicated/API reports are historical unless source hashes match.')
n['new_characters']=added
n['next_implementation']=[s.replace('HP-to-ATK, outgoing healing','HP-to-ATK implemented; remaining outgoing healing') for s in n['next_implementation']]
n['layout'].update(health_reload_fields='EW241 HP-to-ATK marker, EW242 numeric fixed-reload marker; neither is generic stat routing',health_reload_opcode='kind23 force_reload; query107 reload duration readback for tests only',hp_semantics='max_hp matches active raw HP contributions without runtime condition gating; HP conversion appended before caster-based ATK, rank selection excludes conversion',reload_semantics='maximum numeric fixed time before speed buffs; ignore absent values and unresolved lazy targets; force reload skips already pending >0 and interrupts actual charge mode',workspace_bytes=checkpoint['workspace_bytes_per_squad'])
n['completed_health_reload_semantics']=['Recipient effective maximum HP conversion is dynamic, includes expiry and stacks, follows CPU addition order and does not enter ATK ranking','HP effective maximum lookup uses active recipient contributions independently of generic runtime condition routing','Fixed reload numeric scalar/level values, true zero versus missing value, maximum selection, duration expiry, runtime marker and lazy-target behavior','Forced reload through original CPU instant-handler comparison, existing pending reservation preservation, base and changed weapons, charge cancellation and t=0 boundary','Internal-only ATK/defense result field names are rejected as source effects; no GPU-only interpretation of CPU-ignored aliases','Each-frame damage/ammo/reload comparisons and native/PTX full-squad equivalence; raw CPU traces never feed CUDA']
write('research/detail-expansion-next.json',n)
progress_path='research/detail-health-reload-progress.json'
if (ROOT/progress_path).exists():
 progress=read(progress_path);progress.update(catalog_verification_complete=True,ptx_catalog_completed=103,completed_at=now,final_checkpoint='research/detail-health-reload-checkpoint.json')
 progress['pending_process']['status']='completed';progress['next_action']='Catalog verification complete; use the final checkpoint and continue the full all-character/all-effect goal.';write(progress_path,progress)
print(json.dumps({k:checkpoint[k] for k in ('passed','objective_complete','compiled_characters','mechanics_cases','catalog_cases','python_tests_passed','normal_api_total')}))
