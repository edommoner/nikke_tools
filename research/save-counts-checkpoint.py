"""Save verified v15 progress without claiming the all-effect goal is finished."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def raw(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,r):(ROOT/p).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
main=read('research/detail-counts-verification.json');api=read('research/detail-counts-api-verification.json')
assert main['passed'] and len(main['cases'])==70 and not main['cpu_trace_used_as_gpu_input']
for backend in ('native','ptx'):
 cases=[c for c in main['cases'] if c['backend']==backend];assert len(cases)==35 and all(c['passed'] for c in cases)
 assert sum('expected_count' in c for c in cases)==30
 assert all(c['reduction_calls']>0 for c in cases if 'checks' in c)
for r in (main,api):
 assert r['passed']
 for p,h in r['source_sha256'].items():assert sha(p)==h,p
for k in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'):assert api[k],k
reg=raw('research/detail-counts-tests.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==106 and 'skipped=' not in reg
regression_mode='full discovery passed'
if '\nOK' not in reg:
 repair=read('research/detail-counts-regression-repair.json')
 failures=re.findall(r'^(?:FAIL|ERROR): (.+)$',reg,re.M)
 extra=repair['additional']
 assert len(failures)==2 and {f.split(' ')[0] for f in failures}=={repair['test'],extra['test']},failures
 assert 'FAILED (failures=1, errors=1)' in reg
 assert sha(repair['file'])==repair['after_sha256'] and sha('research/detail-counts-test-detail-gpu-before.txt')==repair['before_sha256']
 before=raw('research/detail-counts-test-detail-gpu-before.txt')
 expected=before.replace("e['trigger']={'timing':['hit_count:0'],'condition':[]}","e['trigger']={'timing':['hit_count:not-a-count'],'condition':[]}")
 assert raw(repair['file'])==expected
 rerun=raw('research/detail-counts-repaired-test.log')
 assert 'Ran 1 test in ' in rerun and '\nOK' in rerun and repair['test'] in rerun
 assert sha(extra['file'])==extra['after_sha256'] and sha('research/detail-counts-test-detail-events-before.txt')==extra['before_sha256']
 expected=raw('research/detail-counts-test-detail-events-before.txt').replace("p=self.compile(['on_attack_count:2']);p['effects'][0][TD+1]=0","p=self.compile(['on_attack_count:2']);p['effects'][0][TD+1]=.5")
 assert raw(extra['file'])==expected
 rerun=raw('research/detail-counts-repaired-events-test.log')
 assert 'Ran 1 test in ' in rerun and '\nOK' in rerun and extra['test'] in rerun
 regression_mode='Full discovery: 104 passed, two stale zero-threshold rejection checks failed; only those expectations changed to malformed input rejection, and both tests passed on targeted reruns. No implementation changes after discovery.'
node=raw('research/detail-counts-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-counts.json');assert coverage['supported']==106
audit=read('research/detail-all-effects-audit.json');assert audit['accepted_contexts']==412
old=read('research/detail-control-checkpoint.json')
upstream={p:h for p,h in old['source_sha256'].items() if p.startswith('research/upstream/')}
for p,h in upstream.items():assert sha(p)==h,p
before=read('research/detail-coverage-control.json');was={r['character'] for r in before['results'] if r['supported']}
added=[r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in was];assert added==['홍련 : 흑영']
files=set(main['source_sha256'])|set(api['source_sha256'])|{'research/detail-counts-verification.json','research/detail-counts-api-verification.json','research/detail-counts-tests.log','research/detail-counts-node-tests.log','research/detail-coverage-counts.json','research/detail-counts-ui-fixture.json','tests/test_detail_counts.py','tests/test_detail_gpu.py','research/detail-infinite-ammo-cpu-references.json','scripts/audit-infinite-ammo.py'}
if regression_mode!='full discovery passed':files.update({'research/detail-counts-regression-repair.json','research/detail-counts-test-detail-gpu-before.txt','research/detail-counts-repaired-test.log','research/detail-counts-test-detail-events-before.txt','research/detail-counts-repaired-events-test.log','tests/test_detail_events.py'})
files.add('research/detail-counts-placeholder-audit.json')
catalog=read('research/detail-catalog-verification.json');current_catalog=catalog['passed'] and all(sha(p)==h for p,h in catalog['source_sha256'].items())
if current_catalog:
 assert catalog['compiled_characters']==106 and len(catalog['cases'])==212
 files.add('research/detail-catalog-verification.json')
now=datetime.now(timezone.utc).isoformat()
checkpoint={'generated_at':now,'passed':True,'objective_complete':False,'abi':'detail_counts_v15','compiled_characters':106,'catalog_characters':203,'favorite_contexts_compiled':412,'favorite_contexts_total':812,'compilation_is_not_all_context_parity':True,'new_characters':added,'mechanics_cases':70,'primitive_cases_per_backend':30,'synthetic_squads_per_backend':4,'new_real_squads_per_backend':1,'python_tests_passed':106,'python_test_seconds':float(m[2]),'node_tests_passed':20,'normal_api_total':api['total'],'workspace_bytes_per_squad':api['compute']['workspace_bytes'],'cpu_trace_used_as_gpu_input':False,'current_catalog_verified':current_catalog,'catalog_cases':len(catalog['cases']) if current_catalog else None,'scope':'Dynamic trigger_count_reduce buff including raw timing group identity, fixed-value sum/truncation, expiry/merge/runtime-gate semantics, partial-charge counters and full synthetic/Scarlet Black Shadow squads. Static enemy, bounded supported effects; not every character, favorite or combination.','reports':['research/detail-counts-verification.json','research/detail-counts-api-verification.json','research/detail-counts-tests.log'],'source_sha256':{**{p:sha(p) for p in sorted(files)},**upstream}}
checkpoint['regression_mode']=regression_mode
checkpoint['open_semantic_audits']=['research/detail-counts-placeholder-audit.json']
checkpoint['pending_catalog_session']=None if current_catalog else 88150
write('research/detail-counts-checkpoint.json',checkpoint)
n=read('research/detail-expansion-next.json');n.update(generated_at=now,objective_complete=False);n.pop('current_work',None)
if not current_catalog:
 n['current_work']={'feature':'v15 accepted-catalog CPU parity','catalog_session':88150,'catalog_log':'research/detail-counts-catalog.log','status':'Agent verified handle live; revalidate the same handle rather than inferring liveness from this file','next':'Finish this existing run, then repair detail-counts-placeholder-audit.json before expanding counters/next GPU feature','source_sha256':{p:sha(p) for p in ('app/detail_gpu.py','app/detail_effects.cu','scripts/verify-catalog-detail.py')}}
n['current_checkpoint_path']='research/detail-counts-checkpoint.json';n['new_characters']=added
n['checkpoint'].update(compile_coverage=106,previous=105,favorite_contexts_accepted=412,coverage_path='research/detail-coverage-counts.json',workspace_abi='detail_counts_v15',python_tests_passed=106,node_tests_passed=20,normal_api_counts_gpu_verified=True,normal_api_counts_total=api['total'],count_cases_total=70,current_catalog_verified=current_catalog,accepted_catalog_characters=106 if current_catalog else None,accepted_catalog_full_squad_cases=checkpoint['catalog_cases'],historical_reports_note='Current aggregate: detail-counts-checkpoint.json. Earlier reports are historical unless source hashes match.',regression_status='passed: Python106, Node20, counts70 native/PTX and normal API; current catalog='+str(current_catalog))
n['layout'].update(EW=256,CW=160,EW243='original reducer fixed_value',EW244='trigger_count_reduce marker',EW245_248='per-listener matching reducer-definition bitmap',descriptor6='burst stage for event4; reducible-count flag for other supported counters')
n['completed_trigger_count_semantics']=['Raw original timing-set intersection defines reduction groups','Sum fixed_value once per active same-caster instance, ignore stacks/recipients/runtime gates, then truncate and clamp threshold to one','Expiry and merged-first-definition follow CPU active-instance order','non_full_charge_fire_count uses independent partial-shot event counter']
n['next_infinite_ammo_reference']={'path':'research/detail-infinite-ammo-cpu-references.json','cpu_only':True,'gpu_implemented':False,'cases':4,'cancellations':[4,7,2,3],'remaining':'Presence boolean, reload cancellation without completion, ammo preservation, zero-ammo shooting, last/consume suppression and mode/charge transitions'}
n['next_count_placeholder_audit']={'path':'research/detail-counts-placeholder-audit.json','priority':'Confirm and repair before expanding the counter grammar','scope':'Current raw data has no non-full-charge placeholder occurrence; compiler acceptance for that custom syntax needs correction'}
n['current_checkpoint']={'implemented':n['completed_trigger_count_semantics'],'reports':checkpoint['reports'],'scope':checkpoint['scope'],'remaining':'All-character and all-special-effect migration remains incomplete'}
write('research/detail-expansion-next.json',n)
print(json.dumps({k:v for k,v in checkpoint.items() if k!='source_sha256'},ensure_ascii=True))
