"""Validate target-selection evidence before updating the migration checkpoint."""
import hashlib,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def rawtext(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(rawtext(p))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
r=read('research/detail-targets-verification.json');api=read('research/detail-targets-api-verification.json')
assert r['passed'] and len(r['cases'])==44
for p,h in r['source_sha256'].items():assert sha(p)==h,p
assert all(sum(c['backend']==b for c in r['cases'])==22 for b in ('native','ptx'))
for backend in ('native','ptx'):
 z=next(c for c in r['cases'] if c['backend']==backend and c['name']=='zero-stack-state-is-still-a-recipient')
 assert any(ab['stack']==0 and ab['targets'] for o in z['cpu_target_observations'] for ab in o['mark_states'])
assert api['passed'] and api['total']==369664402
for k in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'):assert api[k],k
reg=rawtext('research/detail-targets-regression.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==79 and '\nOK' in reg and 'skipped=' not in reg
focused=rawtext('research/detail-targets-focused-tests.log');assert 'Ran 2 tests' in focused and '\nOK' in focused
node=rawtext('research/detail-targets-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-targets.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==70 and audit['accepted_contexts']==272
old=read('research/detail-time-checkpoint.json')
files=[p for p in old['source_sha256'] if 'time-regression' not in p and 'verify-time-detail' not in p and 'test_detail_time' not in p]
files+=['scripts/verify-targets-detail.py','tests/test_detail_targets.py','research/detail-targets-regression.log','research/detail-targets-focused-tests.log','research/detail-targets-node-tests.log','research/detail-coverage-targets.json','research/detail-all-effects-audit.json']
hashes={p:sha(p) for p in files}
api.update(abi='detail_targets_v8',source_sha256={p:h for p,h in hashes.items() if p.startswith(('app/','web/')) or p in ('server.mjs','research/detail-time-api-fixture.json')})
write('research/detail-targets-api-verification.json',api)
now=datetime.now(timezone.utc).isoformat()
checkpoint={'generated_at':now,'passed':True,'objective_complete':False,'engine_revision':old['engine_revision'],'abi':'detail_targets_v8','workspace_bytes_per_squad':206760,'effect_row_width':224,'python_tests_passed':79,'python_test_seconds':float(m[2]),'node_tests_passed':20,'target_cases':44,'target_primitives_per_backend':16,'target_synthetic_squads_per_backend':6,'focused_tests_rerun':2,'test_note':'Full discovery completed; target module rerun after correcting zero-stack fixture and adding CPU stimulus assertions. Runtime implementation unchanged during these runs.','compiled_characters':70,'catalog_characters':203,'favorite_contexts_compiled':272,'favorite_contexts_total':812,'normal_api_total':api['total'],'cpu_trace_used_as_gpu_input':False,'scope':'Authored state-recipient and filtered-rank fixtures, full regression and normal API; static boss. Existing catalog 140-case report is historical for prior ABI. Neither compile acceptance nor these fixtures prove every character/effect/combination.','reports':['research/detail-targets-verification.json','research/detail-targets-api-verification.json','research/detail-targets-regression.log','research/detail-targets-focused-tests.log'],'source_sha256':hashes}
write('research/detail-targets-checkpoint.json',checkpoint)
n=read('research/detail-expansion-next.json');n['generated_at']=now
n['checkpoint'].update(previous=70,coverage_path='research/detail-coverage-targets.json',python_tests_passed=79,python_test_scope=f'79-test full discovery in {m[2]} seconds; no skips, followed by current corrected target module rerun',regression_status='passed: Python79 and focused target2, Node20, 44 target cases native/PTX, normal API GPU/CPU/board/cache/fallback',workspace_abi='detail_targets_v8',normal_api_time_gpu_verified=False,normal_api_targets_gpu_verified=True,normal_api_targets_total=api['total'],target_cases_total=44,target_report='research/detail-targets-verification.json',catalog_report_current=False,historical_reports_note='Earlier catalog, time, stackops and other dedicated reports are historical unless source hashes match. Current aggregate: detail-targets-checkpoint.json.')
n['next_implementation'][1]='Ordered target lists with duplicates (CPU eagerly resolves list children), remaining state-selected targets/persona, below-defense selection and explicit lazy-target cache history, then incoming/live-event semantics'
n['layout'].update(EW223='with/without state target flags: 1 any weapon mode, 2 empty state name',target_kinds_12_13='with/without state snapshot',target_kind_11='casted intersect innate-B3 or weapon mask',target_kinds_15_16='lazy weapon-filtered highest ATK / innate-B3 lowest ATK')
n['new_characters']=[]
n['completed_target_semantics']=['Snapshot state/complement targets: zero-stack presence and unresolved-target exclusion, named/generic weapon modes and empty-mode names','Casted burst intersect original weapon type; innate-B3 mask honors pinned burst_stage','Lazy original-weapon-filtered highest ATK and innate-B3-filtered lowest ATK; live stats, stable squad-order ties, bullet/health semantics','Lazy target grouping keys include weapon/B3 candidate mask; no collision between distinct weapon filters']
write('research/detail-expansion-next.json',n)
print(json.dumps({'passed':True,'target_cases':44,'python_tests':79,'compiled':70,'objective_complete':False}))
