"""Validate probability implementation evidence without reducing the full goal."""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def rawtext(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(rawtext(p))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
main=read('research/detail-probability-verification.json');isolation=read('research/detail-probability-isolation.json');catalog=read('research/detail-catalog-verification.json');api=read('research/detail-probability-api-verification.json')
assert main['passed'] and len(main['cases'])==84
assert isolation['passed'] and len(isolation['cases'])==3
assert catalog['passed'] and catalog['compiled_characters']==92 and len(catalog['cases'])==184
for r in (main,isolation,catalog):
 for p,h in r['source_sha256'].items():assert sha(p)==h,p
for b in ('native','ptx'):
 assert sum(c['backend']==b for c in main['cases'])==42
 assert sum(c['backend']==b for c in catalog['cases'])==92
assert api['passed'] and api['total']==481622363
for k in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'):assert api[k],k
reg=rawtext('research/detail-probability-regression.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==91 and '\nOK' in reg and 'skipped=' not in reg
node=rawtext('research/detail-probability-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-probability.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==92 and audit['accepted_contexts']==355
old=read('research/detail-predicates-checkpoint.json')
files=[p for p in old['source_sha256'] if not any(s in p for s in ('predicates-regression','predicates-node','detail-coverage-predicates','detail-stun-cache-audit'))]
files+=['scripts/verify-probability-detail.py','scripts/verify-probability-isolation.py','scripts/verify-detail.py','tests/test_detail_probability.py','research/detail-probability-regression.log','research/detail-probability-node-tests.log','research/detail-coverage-probability.json','research/detail-probability-api-fixture.json','research/detail-probability-ui-fixture.json']
hashes={p:sha(p) for p in files}
for p,h in old['source_sha256'].items():
 if p.startswith('research/upstream/'):assert hashes[p]==h,p
api.update(abi='detail_probability_v11',source_sha256={p:h for p,h in hashes.items() if p.startswith(('app/','web/')) or p in ('server.mjs','research/detail-probability-api-fixture.json')})
write('research/detail-probability-api-verification.json',api)
now=datetime.now(timezone.utc).isoformat();previous=read('research/detail-coverage-predicates.json');was={r['character'] for r in previous['results'] if r['supported']};added=[r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in was]
checkpoint={'generated_at':now,'passed':True,'objective_complete':False,'engine_revision':old['engine_revision'],'abi':'detail_probability_v11','workspace_bytes_per_squad':210856,'effect_row_width':224,'python_tests_passed':91,'python_test_seconds':float(m[2]),'node_tests_passed':20,'probability_cases':84,'primitives_per_backend':22,'synthetic_squads_per_backend':6,'new_real_squads_per_backend':13,'real_shotgun_team_per_backend':1,'native_isolation_cases':3,'catalog_cases':184,'compiled_characters':92,'catalog_characters':203,'favorite_contexts_compiled':355,'favorite_contexts_total':812,'new_characters':added,'normal_api_total':api['total'],'cpu_trace_used_as_gpu_input':False,'rng_mode':'expected; random-roll mode remains unsupported','scope':'Tested expected-mode probability/noncore/context mechanics and static-boss fixtures. Compilation acceptance and one fixed squad per accepted character do not prove all characters/effects/favorite stages/combinations or live boss/incoming semantics.','reports':['research/detail-probability-verification.json','research/detail-probability-isolation.json','research/detail-catalog-verification.json','research/detail-probability-api-verification.json','research/detail-probability-regression.log'],'source_sha256':hashes}
write('research/detail-probability-checkpoint.json',checkpoint)
n=read('research/detail-expansion-next.json');n['generated_at']=now
n['checkpoint'].update(compile_coverage=92,previous=79,favorite_contexts_accepted=355,coverage_path='research/detail-coverage-probability.json',python_tests_passed=91,python_test_scope=f'91-test full discovery in {m[2]} seconds; no skips',regression_status='passed: Python91, Node20, 84 probability cases native/PTX, native isolation3, accepted-catalog184, Tove/Sugar normal API GPU/CPU/board/cache/fallback',workspace_abi='detail_probability_v11',workspace_bytes_per_squad=210856,accepted_catalog_full_squad_cases=184,accepted_catalog_characters=92,catalog_report_current=True,normal_api_predicates_gpu_verified=False,normal_api_probability_gpu_verified=True,normal_api_probability_total=api['total'],probability_cases_total=84,probability_report='research/detail-probability-verification.json',historical_reports_note='Earlier dedicated reports are historical unless source hashes match. Current aggregate: detail-probability-checkpoint.json.')
n['next_implementation'][1]='Remaining charge/cover/camera/ally-HP and other condition constructs; actual named-skill hit/crit contexts, explicit lazy-target cache history, enemy identities/list and state capacities, then live incoming/enemy state'
n['layout'].update(conditions_26_28='26 expected prob, 27 expected not_core, 28 explicit hit_crit',state_probability='chance_acc[NE], noncore_acc[NE] indexed by original effect identity EW58',notify_context='root core_frac/hit_crit parameters; nested DFS frames use empty context and restore parent implicitly',stimulus_fields_6_7='authored core_frac and hit_crit for op0 notifications',query106='readback of original-definition probability/noncore accumulators; output only',workspace_bytes=210856)
n['new_characters']=added
n['completed_probability_semantics']=['Expected accumulation per original effect/caster, independent from active slots and named-state aliases; same-kind repeated conditions share one accumulator','Literal/level-dependent probabilities; missing placeholder false, finite validation, source condition order including self_stat_above preserved','One success at most per condition evaluation, subtraction by one, unclamped finite values and CPU floating threshold phase; max-trigger budget does not suppress condition evaluation','Finite/passive/every/tick-timer evaluation semantics; permanent passive registration still evaluates probability before unconditional registration','Muzzle-level mean of identical per-pellet core probabilities uses runtime-selected CPU sum semantics; hit_count receives snapshot for auto/charge, other root notifications default to empty context','Nested notification context cleared while parent context restored; explicit hit_crit stimulus supported, actual unsupported named-skill notifications remain fail-closed','Standalone CPU oracle explicitly models expected RNG and authored context; accumulator readback is test output, never CPU replay input']
write('research/detail-expansion-next.json',n)
print(json.dumps({'passed':True,'probability_cases':84,'native_isolation_cases':3,'catalog_cases':184,'compiled':92,'python_tests':91,'objective_complete':False}))
