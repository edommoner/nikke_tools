"""Validate and save scoped v16 evidence; the all-character goal remains open."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def raw(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,r):(ROOT/p).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
main=read('research/detail-infinite-verification.json');api=read('research/detail-infinite-api-verification.json')
assert main['passed'] and len(main['cases'])==30 and not main['cpu_trace_used_as_gpu_input']
for backend in ('native','ptx'):
 cases=[c for c in main['cases'] if c['backend']==backend];assert len(cases)==15 and all(c['passed'] for c in cases)
 assert sum(c['name'].startswith('placeholder-') for c in cases)==4
for r in (main,api):
 assert r['passed']
 for p,h in r['source_sha256'].items():assert sha(p)==h,p
for k in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'):assert api[k],k
reg=raw('research/detail-infinite-tests.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==108 and '\nOK' in reg and 'skipped=' not in reg
node=raw('research/detail-infinite-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-infinite.json');assert coverage['supported']==107
audit=read('research/detail-all-effects-audit.json');assert audit['accepted_contexts']==416
old=read('research/detail-counts-checkpoint.json');upstream={p:h for p,h in old['source_sha256'].items() if p.startswith('research/upstream/')}
for p,h in upstream.items():assert sha(p)==h,p
before=read('research/detail-coverage-counts.json');was={r['character'] for r in before['results'] if r['supported']}
added=[r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in was];assert added==['스노우 화이트 : 이노센트 데이즈']
files=set(main['source_sha256'])|set(api['source_sha256'])|{'research/detail-infinite-verification.json','research/detail-infinite-api-verification.json','research/detail-infinite-tests.log','research/detail-infinite-node-tests.log','research/detail-coverage-infinite.json','research/detail-infinite-ui-fixture.json','tests/test_detail_infinite.py','tests/test_detail_gpu.py','tests/test_detail_events.py','scripts/audit-burst-gauge.py','research/detail-burst-gauge-cpu-references.json'}
catalog=read('research/detail-catalog-verification.json');current=catalog['passed'] and all(sha(p)==h for p,h in catalog['source_sha256'].items())
if current:assert catalog['compiled_characters']==107 and len(catalog['cases'])==214
now=datetime.now(timezone.utc).isoformat()
cp={'generated_at':now,'passed':True,'objective_complete':False,'abi':'detail_infinite_v16','compiled_characters':107,'catalog_characters':203,'favorite_contexts_compiled':416,'favorite_contexts_total':812,'compilation_is_not_all_context_parity':True,'new_characters':added,'mechanics_cases':30,'placeholder_cases_per_backend':4,'synthetic_squads_per_backend':10,'new_real_squads_per_backend':1,'python_tests_passed':108,'python_test_seconds':float(m[2]),'node_tests_passed':20,'normal_api_total':api['total'],'workspace_bytes_per_squad':api['compute']['workspace_bytes'],'cpu_trace_used_as_gpu_input':False,'current_catalog_verified':current,'catalog_cases':len(catalog['cases']) if current else None,'scope':'Infinite ammo presence, reload cancellation without refill/completion, ammo/last/consume snapshots, charge/tap/finite weapon mode, unresolved count placeholders with valid mixed timing; static enemy supported squads. Not every character, effect, favorite or combination.','reports':['research/detail-infinite-verification.json','research/detail-infinite-api-verification.json','research/detail-infinite-tests.log'],'source_sha256':{**{p:sha(p) for p in sorted(files)},**upstream}}
write('research/detail-infinite-checkpoint.json',cp)
n=read('research/detail-expansion-next.json');n.update(generated_at=now,objective_complete=False);n.pop('current_work',None);n['current_checkpoint_path']='research/detail-infinite-checkpoint.json';n['new_characters']=added
n['checkpoint'].update(compile_coverage=107,previous=106,favorite_contexts_accepted=416,coverage_path='research/detail-coverage-infinite.json',workspace_abi='detail_infinite_v16',workspace_bytes_per_squad=cp['workspace_bytes_per_squad'],python_tests_passed=108,node_tests_passed=20,infinite_cases_total=30,normal_api_infinite_gpu_verified=True,normal_api_infinite_total=api['total'],current_catalog_verified=current,accepted_catalog_characters=107 if current else None,accepted_catalog_full_squad_cases=cp['catalog_cases'],historical_reports_note='Current aggregate: detail-infinite-checkpoint.json. v15 catalog212 is historical after v16 CUDA change.',regression_status='passed: Python108, Node20, infinite30 native/PTX and normal API; current catalog='+str(current))
n['layout'].update(cached_stat_keys='0..59',workspace_bytes=cp['workspace_bytes_per_squad'],stat59='infinite_ammo boolean presence',descriptor6='Stage for event4; 1 dynamic count reduction, 2 unresolved CPU-never-matching count placeholder on other events',query108='charge/control plus ammo and reloading_until readback')
n['completed_infinite_semantics']=['Presence boolean independent of numeric value','Cancel active reload without refill or completion event; preserve zero ammo shooting','Latch current-shot ammo/last state before callbacks','Keep finite weapon shot limits and normal bullet lifetimes','Unresolved full/nonfull/core/crit/pellet count placeholders never match while retaining index multiplicity']
n['next_count_placeholder_audit']={'status':'Resolved and verified native/PTX','report':'research/detail-infinite-verification.json'}
n['next_infinite_ammo_reference']={'status':'Implemented and verified','report':'research/detail-infinite-verification.json'}
n['next_burst_gauge_reference']={'path':'research/detail-burst-gauge-cpu-references.json','cpu_only':True,'gpu_implemented':False,'cases':10,'next':'Port fixed/accumulate controller, weapon/mode/skill gain and caster first-landed conversion together; no CPU event traces as shader input'}
n['current_checkpoint']={'implemented':n['completed_infinite_semantics'],'reports':cp['reports'],'scope':cp['scope'],'remaining':'All-character and all-special-effect migration remains incomplete'}
write('research/detail-expansion-next.json',n)
print(json.dumps({k:v for k,v in cp.items() if k!='source_sha256'},ensure_ascii=True))
