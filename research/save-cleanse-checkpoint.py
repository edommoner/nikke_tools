"""Finalize scoped v19 evidence; every-character completion remains false."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def raw(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,r):(ROOT/p).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
main=read('research/detail-cleanse-verification.json');nested=read('research/detail-cleanse-nested-verification.json');api=read('research/detail-cleanse-api-verification.json')
assert main['passed'] and len(main['cases'])==104
assert nested['passed'] and len(nested['cases'])==16 and not nested['native_only']
for backend in ('native','ptx'):
 rows=[r for r in main['cases'] if r['backend']==backend];assert len(rows)==52 and all(r['passed'] for r in rows)
 real=[r for r in rows if r['name'].startswith('real-')];assert len(real)==8 and all(r['changed_harmful_instances']>0 for r in real)
 assert len([r for r in nested['cases'] if r['backend']==backend])==8
 assert all(r['checks']['final_health'] for r in nested['cases'] if r['backend']==backend)
files=set()
for report in (main,nested,api):
 assert report['passed']
 if 'cpu_trace_used_as_gpu_input' in report:assert report['cpu_trace_used_as_gpu_input'] is False
 for p,h in report['source_sha256'].items():assert sha(p)==h,p
 files.update(report['source_sha256'])
for key in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback','gauge_modes_separate'):assert api[key],key
reg=raw('research/detail-cleanse-tests.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==114 and '\nOK' in reg and 'skipped=' not in reg
focused=raw('research/detail-cleanse-focused-tests.log');assert re.search(r'Ran 5 tests',focused) and '\nOK' in focused
node=raw('research/detail-cleanse-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-cleanse.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==116 and audit['accepted_contexts']==455
old=read('research/detail-burst-stage-checkpoint.json');upstream={p:h for p,h in old['source_sha256'].items() if p.startswith('research/upstream/')}
for p,h in upstream.items():assert sha(p)==h,p
files.update(['research/detail-cleanse-verification.json','research/detail-cleanse-nested-verification.json','research/detail-cleanse-api-verification.json',
 'research/detail-cleanse-tests.log','research/detail-cleanse-focused-tests.log','research/detail-cleanse-node-tests.log','research/detail-coverage-cleanse.json',
 'research/detail-all-effects-audit.json','research/detail-cleanse-ui-fixture.json','research/detail-cleanse-cpu-references.json','research/detail-cleanse-semantics.json',
 'research/detail-real-cleanse-cpu-references.json','tests/test_detail_cleanse.py'])
before=read('research/detail-coverage-burst-stage.json');was={r['character'] for r in before['results'] if r['supported']}
added=[r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in was]
now=datetime.now(timezone.utc).isoformat()
cp=dict(generated_at=now,passed=True,objective_complete=False,abi='detail_cleanse_v19',compiled_characters=116,catalog_characters=203,
 favorite_contexts_compiled=455,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,new_characters=added,mechanics_cases=104,nested_cases=16,
 python_tests_passed=114,python_test_seconds=float(m[2]),focused_tests_passed=5,node_tests_passed=20,normal_api_total=api['total'],
 workspace_bytes_per_squad=api['compute']['workspace_bytes'],cpu_trace_used_as_gpu_input=False,current_catalog_verified=False,
 scope='Per-recipient oldest harmful-only cleanse, fractional/unlimited limits, partial carriers, no end callbacks, retained timers, live-reference DoT fallback; deterministic compiled targets. Three full raw characters with authored harmful injection; Crust additionally uses authored tap/hold controls. Random targets and every-character parity remain incomplete.',
 reports=['research/detail-cleanse-verification.json','research/detail-cleanse-nested-verification.json','research/detail-cleanse-api-verification.json','research/detail-cleanse-tests.log'])
ui_path='research/detail-cleanse-ui-verification.json'
assert (ROOT/ui_path).exists()
ui=read(ui_path);assert ui['passed']
for p,h in ui['source_sha256'].items():assert sha(p)==h,p
files.add(ui_path);cp.update(normal_ui_verified=True,normal_ui_total=ui['displayed_total'])
cp['source_sha256']={**{p:sha(p) for p in sorted(files)},**upstream};write('research/detail-cleanse-checkpoint.json',cp)
n=read('research/detail-expansion-next.json');n.update(generated_at=now,objective_complete=False,current_checkpoint_path='research/detail-cleanse-checkpoint.json')
n.pop('current_work',None)
n['checkpoint'].update(compile_coverage=116,previous=113,favorite_contexts_accepted=455,coverage_path='research/detail-coverage-cleanse.json',workspace_abi=cp['abi'],
 workspace_bytes_per_squad=cp['workspace_bytes_per_squad'],python_tests_passed=114,python_test_scope=f'114 tests in {m[2]} seconds; no skips',node_tests_passed=20,
 cleanse_cases_total=104,nested_cleanse_cases_total=16,normal_api_cleanse_gpu_verified=True,normal_api_cleanse_total=api['total'],current_catalog_verified=False,
 regression_status='passed: Python114, Node20, cleanse104, nested16, normal API',historical_reports_note='Older all-catalog runs are historical; no current v19 catalog-wide parity claim.')
n['layout'].update(workspace_bytes=cp['workspace_bytes_per_squad'],stat_or_kind26='instant debuff_cleanse',effect255='Scaling DoT original reference state, including empty name for absent scaling_ref')
n.setdefault('next_cleanse_reference',{}).update(cpu_only=False,gpu_implemented=True,random_target_consumers_pending=True,report=cp['reports'][0])
n['current_checkpoint']={'reports':cp['reports'],'scope':cp['scope'],'remaining':'All-character/all-special-effect migration incomplete; random target integration next'}
n['next_action']={'feature':'Integrate seeded GPU random selection and exact lazy/eager target lifecycle','no_live_verification_jobs':True,'plan':'research/detail-random-integration-plan.json'}
write('research/detail-expansion-next.json',n)
print(json.dumps({k:v for k,v in cp.items() if k!='source_sha256'},ensure_ascii=True))
