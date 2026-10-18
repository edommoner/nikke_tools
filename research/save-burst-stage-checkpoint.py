"""Save v18 only after its independent GPU comparisons and regression finish."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def raw(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,r):(ROOT/p).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
main=read('research/detail-burst-stage-verification.json');extra=read('research/detail-all-stage-verification.json');api=read('research/detail-burst-stage-api-verification.json')
assert main['passed'] and len(main['cases'])==112
assert extra['passed'] and len(extra['cases'])==32
for backend in ('native','ptx'):
 rows=[r for r in main['cases'] if r['backend']==backend];assert len(rows)==56 and all(r['passed'] for r in rows)
 real=[r for r in rows if r['name'].startswith('real-')];assert len(real)==6 and all(r['reentry_observed'] for r in real)
 assert len([r for r in extra['cases'] if r['backend']==backend])==16
for report in (main,extra,api):
 assert report['passed']
 for path,digest in report['source_sha256'].items():assert sha(path)==digest,path
for key in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback','gauge_modes_separate'):assert api[key],key
reg=raw('research/detail-burst-stage-tests.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==112 and '\nOK' in reg and 'skipped=' not in reg
node=raw('research/detail-burst-stage-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-burst-stage.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==113 and audit['accepted_contexts']==443
old=read('research/detail-burst-gauge-checkpoint.json');upstream={p:h for p,h in old['source_sha256'].items() if p.startswith('research/upstream/')}
for p,h in upstream.items():assert sha(p)==h,p
files=set(main['source_sha256'])|set(extra['source_sha256'])|set(api['source_sha256'])|{
 'research/detail-burst-stage-verification.json','research/detail-all-stage-verification.json','research/detail-burst-stage-api-verification.json',
 'research/detail-burst-stage-tests.log','research/detail-burst-stage-node-tests.log','research/detail-coverage-burst-stage.json','research/detail-all-effects-audit.json',
 'research/detail-burst-stage-ui-fixture.json','tests/test_detail_burst_stage.py','scripts/verify-burst-gauge-detail.py',
 'research/detail-burst-stage-cpu-references.json','research/detail-all-stage-cpu-references.json'}
now=datetime.now(timezone.utc).isoformat()
cp=dict(generated_at=now,passed=True,objective_complete=False,abi='detail_burst_stage_v18',compiled_characters=113,catalog_characters=203,
 favorite_contexts_compiled=443,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,mechanics_cases=112,all_stage_cases=32,
 python_tests_passed=112,python_test_seconds=float(m[2]),node_tests_passed=20,normal_api_total=api['total'],workspace_bytes_per_squad=api['compute']['workspace_bytes'],
 cpu_trace_used_as_gpu_input=False,current_catalog_verified=False,
 scope='Per-stage once-per-cycle reentry, cooldown reselection, variable stage buffs, A-stage/Red Hood button selection, ally/stage burst notifications, ordered duplicate deferred B3 hits. Static enemy supported squads; not all characters/effects/combinations.',
 reports=['research/detail-burst-stage-verification.json','research/detail-all-stage-verification.json','research/detail-burst-stage-api-verification.json','research/detail-burst-stage-tests.log'],
 source_sha256={**{p:sha(p) for p in sorted(files)},**upstream})
ui_path='research/detail-burst-stage-ui-verification.json'
if (ROOT/ui_path).exists():
 ui=read(ui_path);assert ui['passed']
 for p,h in ui['source_sha256'].items():assert sha(p)==h,p
 cp.update(normal_ui_verified=True,normal_ui_total=ui['displayed_total']);cp['source_sha256'][ui_path]=sha(ui_path)
else:cp['normal_ui_verified']=False
random_path='research/detail-random-verification.json'
if (ROOT/random_path).exists():
 random=read(random_path);assert random['passed'] and not random['combat_integrated'] and not random['oracle_draws_uploaded']
 for p,h in random['source_sha256'].items():assert sha(p)==h,p
 cp.update(isolated_random_prototype_verified=True,isolated_random_operations=sum(r['operations'] for r in random['cases']),isolated_random_combat_integrated=False)
 cp['source_sha256'].update({p:sha(p) for p in random['source_sha256']});cp['source_sha256'][random_path]=sha(random_path)
write('research/detail-burst-stage-checkpoint.json',cp)
n=read('research/detail-expansion-next.json');n.update(generated_at=now,objective_complete=False,current_checkpoint_path='research/detail-burst-stage-checkpoint.json')
n.pop('current_work',None)
n['checkpoint'].update(compile_coverage=113,previous=110,favorite_contexts_accepted=443,coverage_path='research/detail-coverage-burst-stage.json',workspace_abi=cp['abi'],
 workspace_bytes_per_squad=cp['workspace_bytes_per_squad'],python_tests_passed=112,python_test_scope=f'112 tests in {m[2]} seconds; no skips',node_tests_passed=20,
 burst_stage_cases_total=112,all_stage_cases_total=32,normal_api_burst_stage_gpu_verified=True,normal_api_burst_stage_total=api['total'],current_catalog_verified=False,
 regression_status='passed: Python112, Node20, stage112, A-stage32, normal API',historical_reports_note='v15 catalog212 is historical; no current v18 catalog-wide parity claim.')
n['layout'].update(char_row_width=168,workspace_bytes=cp['workspace_bytes_per_squad'],burst_stage_fields='CW160 explicit,161 Red Hood,162 innate initial,163 reentry delay; EW252 override,253 reenter state,254 pending request')
n.setdefault('next_cleanse_reference',{}).update(path='research/detail-cleanse-cpu-references.json',semantics='research/detail-cleanse-semantics.json',cases=22,cpu_only=True,gpu_implemented=False)
n.setdefault('next_harmful_random_reference',{}).update(path='research/detail-harmful-random-cpu-references.json',cases=9,cpu_only=True,gpu_implemented=False)
n['current_checkpoint']={'reports':cp['reports'],'scope':cp['scope'],'remaining':'All-character/all-special-effect migration incomplete'}
write('research/detail-expansion-next.json',n)
print(json.dumps({k:v for k,v in cp.items() if k!='source_sha256'},ensure_ascii=True))
