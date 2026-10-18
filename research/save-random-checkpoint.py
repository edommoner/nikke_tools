"""Gate a scoped v20 checkpoint on independent battles, routing and regression."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def raw(name):
 b=(ROOT/name).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(name):return json.loads(raw(name))
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def write(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=['research/detail-random-target-native-verification.json','research/detail-random-target-ptx-verification.json'];reports=[read(p) for p in paths]
for backend,report in zip(('native','ptx'),reports):
 assert report['passed'] and not report['quick']
 assert len(report['cases'])==122 and all(r['passed'] and r['backend']==backend and r['checks']['final_random_state'] for r in report['cases'])
 assert len([r for r in report['cases'] if r['name']=='real-cocoa-positive-cleanse'])==6
 assert report['cpu_trace_used_as_gpu_input'] is False
 for name,digest in report['source_sha256'].items():assert sha(name)==digest,name
nested_path='research/detail-random-nested-verification.json';nested=read(nested_path)
assert nested['passed'] and len(nested['cases'])==16 and all(r['checks']['final_health'] for r in nested['cases'])
for name,digest in nested['source_sha256'].items():assert sha(name)==digest,name
positive=read('research/detail-random-real-positive.json');assert positive['passed'] and len(positive['cases'])==6
assert all(r['positive_random_picks']>0 and r['changed_harmful_instances']>0 for r in positive['cases'])
reg=raw('research/detail-random-tests.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==118 and '\nOK' in reg and 'skipped=' not in reg
for line in reg.splitlines():
 if line.startswith('{'):
  try:r=json.loads(line)
  except ValueError:continue
  assert r.get('passed') is not False,r.get('name')
node=raw('research/detail-random-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
api_path='research/detail-random-api-verification.json';ui_path='research/detail-random-ui-verification.json'
api=read(api_path);ui=read(ui_path)
for report in (api,ui):
 assert report['passed']
 for name,digest in report['source_sha256'].items():assert sha(name)==digest,name
for key in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback','seed_cache_separated','gauge_modes_separate'):assert api[key],key
coverage=read('research/detail-coverage-random.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==117 and audit['accepted_contexts']==459
upstream={p:h for p,h in read('research/detail-cleanse-checkpoint.json')['source_sha256'].items() if p.startswith('research/upstream/')}
for p,h in upstream.items():assert sha(p)==h,p
now=datetime.now(timezone.utc).isoformat()
cp=dict(generated_at=now,passed=True,objective_complete=False,abi='detail_random_v20',compiled_characters=117,catalog_characters=203,favorite_contexts_compiled=459,favorite_contexts_total=812,
 compilation_is_not_all_context_parity=True,current_catalog_verified=False,random_battle_cases=244,nested_health_cases=16,final_mt_state_verified=True,raw_cocoa_positive_cases=12,
 python_tests_passed=118,python_test_seconds=float(m[2]),node_tests_passed=20,normal_api_total=api['total'],normal_ui_total=ui['displayed_total'],normal_ui_verified=True,
 seed_contract='uint32, default 0 shared by independent CPU/GPU executions',random_cache_entries=1024,cache_overflow='reject complete GPU result; fallback CPU',
 workspace_bytes_per_squad=api['compute']['workspace_bytes'],cpu_trace_used_as_gpu_input=False,
 scope='Static unharmed boss, expected damage mode. Exact seeded small-pool sample, eager/lazy target lifecycle, shared persistent cache, trigger probes/budgets, ordered lists, periodic instants and DoT, expiration logging, full-burst snapshot and per-query special ATK; raw Cocoa positive tests retain all skills. Every-character/effect migration remains incomplete.',reports=paths+[nested_path,api_path,ui_path,'research/detail-random-tests.log'])
files=set(['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py','web/app.js','web/index.html','tests/test_detail_random.py','scripts/verify-random-target-detail.py','scripts/smoke-detail.mjs',
 *cp['reports'],'research/detail-random-real-positive.json','research/detail-coverage-random.json','research/detail-all-effects-audit.json','research/detail-random-node-tests.log'])
cp['source_sha256']={**{p:sha(p) for p in sorted(files)},**upstream};write('research/detail-random-checkpoint.json',cp)
n=read('research/detail-expansion-next.json');n.update(generated_at=now,objective_complete=False,current_checkpoint_path='research/detail-random-checkpoint.json');n.pop('current_work',None)
n['checkpoint'].update(compile_coverage=117,previous=116,favorite_contexts_accepted=459,coverage_path='research/detail-coverage-random.json',workspace_abi=cp['abi'],workspace_bytes_per_squad=cp['workspace_bytes_per_squad'],python_tests_passed=118,python_test_scope=f'118 tests in {m[2]} seconds; no skips',node_tests_passed=20,current_catalog_verified=False,regression_status='passed: Python118, Node20, random244 with final MT state, normal API/UI',historical_reports_note='Older catalog-wide reports are historical; current v20 all-catalog parity not claimed.')
n['layout'].update(effect_row_width=264,workspace_bytes=cp['workspace_bytes_per_squad'],random_cache_entries=1024)
n['current_checkpoint']={'reports':cp['reports'],'scope':cp['scope'],'remaining':'Every-character/effect migration incomplete; static-boss and capacity bounds remain.'}
n['next_action']={'feature':'Audit squad-composition predicates, then shield/range lifecycle and catalog-wide parity','plan':'research/detail-squad-condition-plan.json','no_live_verification_jobs':True}
write('research/detail-expansion-next.json',n)
plan=read('research/detail-random-integration-plan.json');plan.update(combat_integrated=True,prototype_status='integrated seeded small-pool target PRNG verified in full battles',seed_contract=cp['seed_contract'],battle_report=paths,objective_complete=False);write('research/detail-random-integration-plan.json',plan)
print(json.dumps({k:v for k,v in cp.items() if k!='source_sha256'},ensure_ascii=True))
