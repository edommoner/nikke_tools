"""Scoped composition predicate evidence; every-character goal stays incomplete."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def raw(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,r):(ROOT/p).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
main=read('research/detail-squad-condition-verification.json');api=read('research/detail-squad-api-verification.json');ui=read('research/detail-squad-ui-verification.json')
assert main['passed'] and not main['quick'] and not main['native_only'] and len(main['cases'])==160
assert main['cpu_trace_used_as_gpu_input'] is False
for backend in ('native','ptx'):
 rows=[r for r in main['cases'] if r['backend']==backend];assert len(rows)==80 and all(r['passed'] and r['checks']['final_random_state'] for r in rows)
 real=[r for r in rows if 'condition_exercised' in r['checks']];assert len(real)==16 and all(r['checks']['condition_exercised'] for r in real)
 assert sum(r.get('authored_supporter_without_skills')=='렘' for r in real)==4
for report in (main,api,ui):
 assert report['passed']
 for p,h in report['source_sha256'].items():assert sha(p)==h,p
for key in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback','seed_cache_separated','gauge_modes_separate','shooting_modes_separate'):assert api[key],key
reg=raw('research/detail-squad-tests.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg);assert m and int(m[1])==120 and '\nOK' in reg and 'skipped=' not in reg
for line in reg.splitlines():
 if line.startswith('{'):
  try:r=json.loads(line)
  except ValueError:continue
  assert r.get('passed') is not False,r.get('name')
node=raw('research/detail-squad-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-squad.json');audit=read('research/detail-all-effects-audit.json');assert coverage['supported']==119 and audit['accepted_contexts']==467
before=read('research/detail-random-checkpoint.json');unchanged={p:h for p,h in before['source_sha256'].items() if p.startswith('research/upstream/') or p in ('app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json')}
for p,h in unchanged.items():assert sha(p)==h,p
now=datetime.now(timezone.utc).isoformat();paths=['research/detail-squad-condition-verification.json','research/detail-squad-api-verification.json','research/detail-squad-ui-verification.json','research/detail-squad-tests.log']
cp=dict(generated_at=now,passed=True,objective_complete=False,feature='v21 squad affiliation predicate',abi='detail_random_v20',abi_unchanged=True,kernel_unchanged=True,
 compiled_characters=119,catalog_characters=203,favorite_contexts_compiled=467,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,current_catalog_verified=False,
 predicate_cases=160,raw_subject_cases=32,raw_noir_full_squad_cases=16,raw_ram_controlled_rem_cases=8,python_tests_passed=120,python_test_seconds=float(m[2]),node_tests_passed=20,
 normal_api_total=api['total'],normal_ui_total=ui['displayed_total'],normal_ui_verified=True,cpu_trace_used_as_gpu_input=False,
 scope='Immutable original-name squad metadata predicate lowered to a GPU literal condition. Matches pinned CPU registration/runtime semantics, including passive static-condition behavior. Full Noir skills with/without Rouge; full Ram skills with negative real squads and positive authored supporter Rem whose unsupported skills are explicitly removed only in verification. Full Ram+Rem production GPU support remains incomplete.',reports=paths)
files=set(paths+['app/detail_gpu.py','tests/test_detail_squad.py','scripts/verify-squad-condition-detail.py','scripts/audit-squad-condition.py','research/detail-squad-condition-cpu-references.json','research/detail-squad-node-tests.log','research/detail-coverage-squad.json','research/detail-all-effects-audit.json'])
cp['source_sha256']={**{p:sha(p) for p in sorted(files)},**unchanged};write('research/detail-squad-checkpoint.json',cp)
n=read('research/detail-expansion-next.json');n.update(generated_at=now,objective_complete=False,current_checkpoint_path='research/detail-squad-checkpoint.json');n.pop('current_work',None)
n['checkpoint'].update(compile_coverage=119,previous=117,favorite_contexts_accepted=467,coverage_path='research/detail-coverage-squad.json',python_tests_passed=120,python_test_scope=f'120 tests in {m[2]} seconds; no skips',node_tests_passed=20,regression_status='passed: Python120, Node20, squad160, normal API/UI',current_catalog_verified=False)
n['current_checkpoint']={'reports':paths,'scope':cp['scope'],'remaining':'All-character/effect migration incomplete; Rem, shields, range, boss interactions and all-context parity remain.'}
n['next_action']={'feature':'Audit remaining shield/undying/range effects and current accepted-catalog parity','no_live_verification_jobs':True}
write('research/detail-expansion-next.json',n)
print(json.dumps({k:v for k,v in cp.items() if k!='source_sha256'},ensure_ascii=True))
