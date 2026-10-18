"""Require current predicate, element-branch, catalog, API and regression proof."""
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def rawtext(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(rawtext(p))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
main=read('research/detail-predicates-verification.json');codes=read('research/detail-enemy-codes-verification.json');stimuli=read('research/detail-predicate-stimuli.json');mixes=read('research/detail-predicate-mixes-verification.json');catalog=read('research/detail-catalog-verification.json');api=read('research/detail-predicates-api-verification.json')
assert main['passed'] and len(main['cases'])==64
assert codes['passed'] and len(codes['cases'])==12 and all(c['code_branch_exercised'] for c in codes['cases'])
assert stimuli['passed'] and len(stimuli['primitives'])==17 and any(s['selected'] for s in stimuli['real_persona']['selections'])
assert mixes['passed'] and len(mixes['cases'])==12 and len(mixes['inputs'])==6
assert catalog['passed'] and catalog['compiled_characters']==79 and len(catalog['cases'])==158
for r in (main,codes,stimuli,mixes,catalog):
 for p,h in r['source_sha256'].items():assert sha(p)==h,p
for b in ('native','ptx'):
 assert sum(c['backend']==b for c in main['cases'])==32
 assert sum(c['backend']==b for c in codes['cases'])==6
 assert sum(c['backend']==b for c in mixes['cases'])==6
 assert sum(c['backend']==b for c in catalog['cases'])==79
assert api['passed'] and api['total']==stimuli['real_persona']['cpu_total']==997057331
for k in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'):assert api[k],k
reg=rawtext('research/detail-predicates-regression.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==88 and '\nOK' in reg and 'skipped=' not in reg
node=rawtext('research/detail-predicates-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-predicates.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==79 and audit['accepted_contexts']==309
old=read('research/detail-lists-checkpoint.json')
files=[p for p in old['source_sha256'] if not any(x in p for x in ('lists-regression','lists-node','detail-coverage-lists','detail-list-plan-audit'))]
files+=['scripts/verify-predicates-detail.py','scripts/verify-enemy-codes-detail.py','scripts/verify-predicate-stimuli.py','scripts/verify-predicate-mixes.py','tests/test_detail_predicates.py','research/detail-predicates-regression.log','research/detail-predicates-node-tests.log','research/detail-coverage-predicates.json','research/detail-predicates-api-fixture.json','research/detail-predicates-ui-fixture.json','research/detail-stun-cache-audit.json']
hashes={p:sha(p) for p in files}
for p,h in old['source_sha256'].items():
 if p.startswith('research/upstream/'):assert hashes[p]==h,p
api.update(abi='detail_predicates_v10',source_sha256={p:h for p,h in hashes.items() if p.startswith(('app/','web/')) or p in ('server.mjs','research/detail-predicates-api-fixture.json')})
write('research/detail-predicates-api-verification.json',api)
now=datetime.now(timezone.utc).isoformat();oldcoverage=read('research/detail-coverage-lists.json');previous={r['character'] for r in oldcoverage['results'] if r['supported']};added=[r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in previous]
checkpoint={'generated_at':now,'passed':True,'objective_complete':False,'engine_revision':old['engine_revision'],'abi':'detail_predicates_v10','workspace_bytes_per_squad':208808,'effect_row_width':224,'python_tests_passed':88,'python_test_seconds':float(m[2]),'node_tests_passed':20,'predicate_cases':64,'predicate_primitives_per_backend':17,'predicate_synthetic_squads_per_backend':7,'predicate_new_real_squads_per_backend':7,'predicate_real_mixed_squads_per_backend':1,'real_enemy_code_cases':12,'catalog_cases':158,'compiled_characters':79,'catalog_characters':203,'favorite_contexts_compiled':309,'favorite_contexts_total':812,'new_characters':added,'normal_api_total':api['total'],'cpu_trace_used_as_gpu_input':False,'scope':'Static single-boss fixtures, element branches, tested mechanics and one fixed grown squad per accepted character; not all characters/effects/favorite stages/combinations or live boss/add/incoming semantics. Compilation acceptance is not global parity.','reports':['research/detail-predicates-verification.json','research/detail-enemy-codes-verification.json','research/detail-predicate-stimuli.json','research/detail-catalog-verification.json','research/detail-predicates-api-verification.json','research/detail-predicates-regression.log'],'source_sha256':hashes}
checkpoint['seeded_mix_cases']=12;checkpoint['reports'].append('research/detail-predicate-mixes-verification.json');write('research/detail-predicates-checkpoint.json',checkpoint)
n=read('research/detail-expansion-next.json');n['generated_at']=now
n['checkpoint'].update(compile_coverage=79,previous=72,favorite_contexts_accepted=309,coverage_path='research/detail-coverage-predicates.json',python_tests_passed=88,python_test_scope=f'88-test full discovery in {m[2]} seconds; no skips',regression_status='passed: Python88, Node20, 64 predicate cases, 12 real enemy-code branches, 158 accepted-catalog full squads native/PTX, persona normal API GPU/CPU/board/cache/fallback',workspace_abi='detail_predicates_v10',workspace_bytes_per_squad=208808,accepted_catalog_full_squad_cases=158,accepted_catalog_characters=79,catalog_report_current=True,normal_api_lists_gpu_verified=False,normal_api_predicates_gpu_verified=True,normal_api_predicates_total=api['total'],predicate_cases_total=64,predicate_report='research/detail-predicates-verification.json',enemy_code_report='research/detail-enemy-codes-verification.json',historical_reports_note='Earlier dedicated reports are historical unless source hashes match. Current aggregate: detail-predicates-checkpoint.json.')
n['next_implementation'][1]='Remaining probability/core/charge/cover/camera and other condition constructs; explicit lazy-target cache history, enemy identities in target lists and capacity expansion; live incoming/enemy state remains open'
n['layout'].update(target_kind_14='lazy allies_below_def: effective defense, strict comparison, squad order',target_kind_18='innate B3 persona marker members excluding caster; eager snapshot',EW213='marker flags: 1 persona_state, 2 stun_immune',conditions_22_25='22 static single-boss runtime code/count, 23 activation enemy stun, 24 activation self stun immunity, 25 activation boss/add',self_state_condition_arg='1 generic weapon mode, 2 empty mode name, 0 exact state name')
n['new_characters']=added
n['completed_predicate_semantics']=['Friendly defense percentage remains numeric for raw effective-defense selection while excluded from outgoing enemy-defense routing; caster-base flat defense and recipient stacks preserved','Below-defense strict comparison uses raw active final defense; top-defense retains pinned base-stat sorting; strings lazy, list children eager','Persona markers: active recipient membership independent of zero stack, unresolved targets excluded, innate B3 and caster exclusion','Enemy code missing/matched/mismatched and static one-enemy count gates; boss/add activation gates remain distinct from runtime gates','Raw stun membership and immunity do not force lazy resolution; zero-duration same-frame stun, immunity expiry, and activation-latched conditions match CPU','Persistent self-state tests include generic/named weapon mode and empty mode-name semantics']
write('research/detail-expansion-next.json',n)
print(json.dumps({'passed':True,'predicate_cases':64,'real_code_cases':12,'catalog_cases':158,'compiled':79,'python_tests':88,'objective_complete':False}))
