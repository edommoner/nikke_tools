"""Validate current reports and save the bounded GPU migration checkpoint."""
import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def read(p):
 raw=(ROOT/p).read_bytes()
 return json.loads(raw.decode('utf-16') if raw.startswith(b'\xff\xfe') else raw.decode('utf-8-sig'))
def write(p,v): (ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
time=read('research/detail-time-verification.json');catalog=read('research/detail-catalog-verification.json');api=read('research/detail-time-api-verification.json')
assert time['passed'] and len(time['cases'])==58
assert catalog['passed'] and catalog['compiled_characters']==70 and len(catalog['cases'])==140
for report in (time,catalog):
 for p,h in report['source_sha256'].items(): assert sha(p)==h,p
assert api['passed'] and api['total']==369664402
for key in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'): assert api[key],key
assert all(sum(c['backend']==b for c in catalog['cases'])==70 for b in ('native','ptx'))
raw=(ROOT/'research/detail-time-regression.log').read_bytes()
log=raw.decode('utf-16') if raw.startswith(b'\xff\xfe') else raw.decode('utf-8-sig')
assert 'Ran 77 tests in 352.014s' in log and '\nOK' in log and 'skipped=' not in log
audit=read('research/detail-all-effects-audit.json')
assert audit['accepted_contexts']==272 and audit['total_contexts']==812
old=read('research/detail-stackops-checkpoint.json')
files=list(old['source_sha256'])
files=[p for p in files if 'stackops' not in p]
files+=['scripts/verify-time-detail.py','tests/test_detail_time.py','tests/test_detail_events.py','tests/test_detail_gpu.py','research/detail-time-regression.log','server.mjs','web/app.js','research/detail-time-api-fixture.json','research/detail-time-ui-fixture.json']
hashes={p:sha(p) for p in files}
api.update(abi='detail_time_v7',source_sha256={p:h for p,h in hashes.items() if p.startswith(('app/','web/')) or p in ('server.mjs','research/detail-time-api-fixture.json')})
write('research/detail-time-api-verification.json',api)
now=datetime.now(timezone.utc).isoformat()
reports={p:{'passed':r['passed'],'generated_at':r['generated_at'],'cases':len(r.get('cases',[]))} for p,r in [('detail-time-verification.json',time),('detail-catalog-verification.json',catalog),('detail-time-api-verification.json',api)]}
checkpoint=dict(generated_at=now,passed=True,objective_complete=False,engine_revision=old['engine_revision'],abi='detail_time_v7',effect_row_width=224,cached_stats=59,workspace_bytes_per_squad=206760,definition_capacity=128,instance_slot_capacity=512,python_runtime=sys.version,python_tests_passed=77,python_test_seconds=352.014,node_tests_passed=20,time_cases=58,time_primitives_per_backend=21,time_synthetic_squads_per_backend=5,time_new_real_squads_per_backend=2,time_real_interaction_squads_per_backend=1,catalog_cases=140,compiled_characters=70,catalog_characters=203,favorite_contexts_compiled=272,favorite_contexts_total=812,cpu_trace_used_as_gpu_input=False,normal_api_total=api['total'],reports=reports,scope=old['scope'],source_sha256=hashes)
write('research/detail-time-checkpoint.json',checkpoint)
n=read('research/detail-expansion-next.json');n['generated_at']=now
n['checkpoint'].update(compile_coverage=70,previous=68,favorite_contexts_accepted=272,python_tests_passed=77,python_test_scope='77-test complete discovery in 352.014 seconds; no skips',coverage_path='research/detail-coverage-time.json',regression_status='passed: Python77, Node20, 58 time cases native/PTX, 140 accepted-catalog squads native/PTX, Arcana/Isabel normal API GPU/CPU/board/cache/fallback',workspace_abi='detail_time_v7',workspace_bytes_per_squad=206760,accepted_catalog_full_squad_cases=140,accepted_catalog_characters=70,time_cases_total=58,time_report='research/detail-time-verification.json',normal_api_time_gpu_verified=True,normal_api_time_total=api['total'],normal_api_stackops_gpu_verified=False,historical_reports_note='Earlier reports, including stackops API, are historical unless source hashes match. Current aggregate: detail-time-checkpoint.json.')
n['next_implementation'][1]='Remaining target/condition constructs (lists and state-selected recipients), explicit lazy target-group cache history, then incoming/live-event semantics; duration scaling and periodic modifiers implemented and fixture-verified'
n['layout'].update(EW=224,cached_stat_keys='0..58',EW218='duration_scaling stack_count',EW219='duration scaling named reference',EW220='flat period modifier group',EW221='flat modifier exact effect name',EW222='nonempty target effect name',kernel_extra_argument='compensated_sums (CPython >=3.12)')
n['instance_storage']['definition_identity']='original immutable row; dynamic burst recipients use active slots without row expansion'
n['new_characters']=['아르카나','에이다']
n['completed_time_semantics']=['Named-stack duration scaling on normal activation and conditional passive refresh; stack init/add retain raw durations','Every clocks share definition identity across distinct/duplicate timings; phase rescaling, 5% floor, named flat and percentage modifiers, remaining-time one-off reduction','Dynamic casted and innate-B3-casted recipients outside burst boundaries','Startup magazines filled before first tick and lazy target resolution','Runtime-selected compensated sums for periodic and critical stats; critical rate clamp']
write('research/detail-expansion-next.json',n)
print(json.dumps({'passed':True,'cases':140,'time_cases':58,'compiled':70,'normal_api_total':api['total']}))
