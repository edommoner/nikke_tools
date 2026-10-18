"""Save only current verified mode evidence; preserve the unfinished full scope."""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def raw(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
main=read('research/detail-modes-verification.json')
assert main['passed'] and len(main['cases'])==42
for p,h in main['source_sha256'].items():assert sha(p)==h,p
for backend in ('native','ptx'):assert sum(c['backend']==backend for c in main['cases'])==21
reg=raw('research/detail-modes-tests.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==94 and '\nOK' in reg and 'skipped=' not in reg
assert 'pass 20' in raw('research/detail-modes-node-tests.log') and 'fail 0' in raw('research/detail-modes-node-tests.log')
api=read('research/detail-modes-api-verification.json');demo=read('research/detail-gpu-demo-api-verification.json');bursts=read('research/detail-burst-lists-verification.json')
assert api['passed'] and demo['passed'] and bursts['passed']
for r in (api,demo):
 for key in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'):assert r[key],key
for r in (demo,bursts):
 for p,h in r['source_sha256'].items():assert sha(p)==h,p
coverage=read('research/detail-coverage-modes.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==98 and audit['accepted_contexts']==379
old=read('research/detail-probability-checkpoint.json')
for p,h in old['source_sha256'].items():
 if p.startswith('research/upstream/'):assert sha(p)==h,p
before=read('research/detail-coverage-probability.json');was={r['character'] for r in before['results'] if r['supported']}
added=[r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in was]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/engine_compat.py','app/gpu_service.py','server.mjs','web/app.js','web/index.html','scripts/verify-detail.py','scripts/verify-modes-detail.py','scripts/verify-burst-lists-detail.py','tests/test_detail_modes.py','research/detail-modes-tests.log','research/detail-modes-node-tests.log','research/detail-modes-api-fixture.json','research/detail-modes-ui-fixture.json']
hashes={p:sha(p) for p in files};hashes.update({p:h for p,h in old['source_sha256'].items() if p.startswith('research/upstream/')})
api.update(abi='detail_modes_v12',source_sha256={p:h for p,h in hashes.items() if p.startswith(('app/','web/')) or p in ('server.mjs','research/detail-modes-api-fixture.json')});write('research/detail-modes-api-verification.json',api)
now=datetime.now(timezone.utc).isoformat()
checkpoint={'generated_at':now,'passed':True,'objective_complete':False,'engine_revision':old['engine_revision'],'abi':'detail_modes_v12','effect_row_width':256,'compiled_characters':98,'catalog_characters':203,'favorite_contexts_compiled':379,'favorite_contexts_total':812,'compilation_is_not_parity':True,'new_characters':added,'mode_cases':42,'synthetic_full_squads_per_backend':15,'new_real_full_squads_per_backend':6,'burst_list_cases':10,'python_tests_passed':94,'python_test_seconds':float(m[2]),'node_tests_passed':20,'normal_api_total':api['total'],'normal_gpu_demo_total':demo['total'],'workspace_bytes_per_squad':demo['compute']['workspace_bytes'],'cpu_trace_used_as_gpu_input':False,'scope':'Static enemy, expected mode, auto full-charge shooting. New mode fixtures, existing full regression, actual burst priorities and normal API verified. Prior 92-character catalog report is historical for the previous CUDA source; this checkpoint does not claim a new full 98-character catalog parity sweep. All characters/effects/favorite stages/cubes and live enemy models remain incomplete.','reports':['research/detail-modes-verification.json','research/detail-modes-tests.log','research/detail-modes-api-verification.json','research/detail-gpu-demo-api-verification.json','research/detail-burst-lists-verification.json'],'source_sha256':hashes}
write('research/detail-modes-checkpoint.json',checkpoint)
n=read('research/detail-expansion-next.json');n['generated_at']=now;n['objective_complete']=False
n['checkpoint'].update(compile_coverage=98,previous=92,favorite_contexts_accepted=379,coverage_path='research/detail-coverage-modes.json',workspace_abi='detail_modes_v12',effect_row_width=256,workspace_bytes_per_squad=checkpoint['workspace_bytes_per_squad'],python_tests_passed=94,python_test_scope=f'94 tests in {m[2]} seconds; no skips',regression_status='passed: Python94, Node20, mode squads42 native/PTX, burst priorities10, normal API mode fixture and updated GPU demo',catalog_report_current=False,normal_api_demo_gpu_verified=True,normal_api_demo_total=demo['total'],normal_api_modes_gpu_verified=True,normal_api_modes_total=api['total'],mode_cases_total=42,mode_report='research/detail-modes-verification.json',historical_reports_note='Current aggregate: detail-modes-checkpoint.json. Earlier reports, including the accepted-catalog sweep, are historical unless source hashes match.')
n['new_characters']=added
n['next_implementation']=[s.replace('finite weapon modes, ','remaining weapon-mode toggle/live gauge semantics, ') for s in n['next_implementation']]
n['layout'].update(mode_fields='EW224..240: fire mode, charge base/multiplier/delay/core, cover reload, shot limit, magazine rules/ref, skill/first coefficient, reload/entry policy',mode_state='mode_shots, mode_ammo snapshot, mode_restored, reload_in_mode, separate charge_post',workspace_bytes=checkpoint['workspace_bytes_per_squad'])
write('research/detail-expansion-next.json',n)
print(json.dumps({k:checkpoint[k] for k in ('passed','objective_complete','compiled_characters','mode_cases','python_tests_passed','normal_api_total','normal_gpu_demo_total')}))
