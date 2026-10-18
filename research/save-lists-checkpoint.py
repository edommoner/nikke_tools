"""Require current list, catalog, API, and regression evidence before checkpoint."""
import json,hashlib,re,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def rawtext(p):
 b=(ROOT/p).read_bytes();return b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
def read(p):return json.loads(rawtext(p))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
lists=read('research/detail-lists-verification.json');catalog=read('research/detail-catalog-verification.json');api=read('research/detail-lists-api-verification.json')
assert lists['passed'] and len(lists['cases'])==54
assert catalog['passed'] and catalog['compiled_characters']==72 and len(catalog['cases'])==144
for report in (lists,catalog):
 for p,h in report['source_sha256'].items():assert sha(p)==h,p
for b in ('native','ptx'):
 assert sum(c['backend']==b for c in lists['cases'])==27
 assert sum(c['backend']==b for c in catalog['cases'])==72
 assert next(c for c in lists['cases'] if c['backend']==b and c['name']=='full-duplicate-hp-buff-postprocessing')['duplicate_hp_posts_exercised']
assert api['passed'] and api['total']==300962258
for k in ('normal_compare_gpu','cpu_verification','board_gpu','cache_separated','unsupported_cpu_fallback'):assert api[k],k
ref=read('research/detail-lists-api-cpu-reference.json');assert ref['total']==api['total'] and ref['fixture_sha256']==sha('research/detail-lists-api-fixture.json')
reg=rawtext('research/detail-lists-regression.log');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',reg)
assert m and int(m[1])==85 and '\nOK' in reg and 'skipped=' not in reg
node=rawtext('research/detail-lists-node-tests.log');assert 'pass 20' in node and 'fail 0' in node
coverage=read('research/detail-coverage-lists.json');audit=read('research/detail-all-effects-audit.json')
assert coverage['supported']==72 and audit['accepted_contexts']==280
plans=read('research/detail-list-plan-audit.json');assert plans['passed'] and len(plans['cases'])==72
assert plans['source_sha256']['app/detail_gpu.py']==sha('app/detail_gpu.py')
old=read('research/detail-targets-checkpoint.json')
files=[p for p in old['source_sha256'] if 'targets-regression' not in p and 'targets-focused' not in p and 'targets-node' not in p and 'detail-coverage-targets' not in p]
files+=['app/engine_compat.py','scripts/verify-lists-detail.py','scripts/verify-catalog-detail.py','tests/test_detail_lists.py','research/detail-lists-regression.log','research/detail-lists-node-tests.log','research/detail-coverage-lists.json','research/detail-lists-api-fixture.json','research/detail-lists-ui-fixture.json','research/detail-lists-api-cpu-reference.json','research/detail-list-plan-audit.json','scripts/smoke-detail.mjs']
hashes={p:sha(p) for p in files}
# Check the pinned CPU files against the prior checkpoint: no vendor edits.
for p,h in old['source_sha256'].items():
 if p.startswith('research/upstream/'):assert hashes[p]==h,p
api.update(abi='detail_lists_v9',source_sha256={p:h for p,h in hashes.items() if p.startswith(('app/','web/')) or p in ('server.mjs','research/detail-lists-api-fixture.json')})
write('research/detail-lists-api-verification.json',api)
now=datetime.now(timezone.utc).isoformat()
checkpoint={'generated_at':now,'passed':True,'objective_complete':False,'engine_revision':old['engine_revision'],'abi':'detail_lists_v9','workspace_bytes_per_squad':208808,'effect_row_width':224,'ordered_target_bits':64,'ordered_target_capacity':21,'definition_and_target_row_capacity':128,'python_tests_passed':85,'python_test_seconds':float(m[2]),'node_tests_passed':20,'list_cases':54,'list_primitives_per_backend':17,'list_synthetic_squads_per_backend':8,'list_new_real_squads_per_backend':2,'catalog_cases':144,'compiled_characters':72,'catalog_characters':203,'favorite_contexts_compiled':280,'favorite_contexts_total':812,'new_characters':['소다 : 트윙클링 바니','마스트'],'normal_api_total':api['total'],'cpu_trace_used_as_gpu_input':False,'cpu_compat':'CharacterLookup membership for raw list instant logging uses existing caster fallback; target resolution/order/identity preserved; vendor files unchanged','scope':'Static-boss fixtures and tested mechanics. Compile acceptance and one fixed grown squad per accepted character do not prove all characters, effects, favorite stages or combinations. Enemy-containing lists and larger capacities remain open.','reports':['research/detail-lists-verification.json','research/detail-catalog-verification.json','research/detail-lists-api-verification.json','research/detail-lists-regression.log'],'source_sha256':hashes}
write('research/detail-lists-checkpoint.json',checkpoint)
n=read('research/detail-expansion-next.json');n['generated_at']=now
n['checkpoint'].update(compile_coverage=72,previous=70,favorite_contexts_accepted=280,coverage_path='research/detail-coverage-lists.json',python_tests_passed=85,python_test_scope=f'85-test full discovery in {m[2]} seconds; no skips',regression_status='passed: Python85, Node20, 54 list cases native/PTX, 144 accepted-catalog full squads native/PTX, normal Mast API GPU/CPU/board/cache/fallback',workspace_abi='detail_lists_v9',workspace_bytes_per_squad=208808,accepted_catalog_full_squad_cases=144,accepted_catalog_characters=72,catalog_report_current=True,normal_api_targets_gpu_verified=False,normal_api_lists_gpu_verified=True,normal_api_lists_total=api['total'],list_cases_total=54,list_report='research/detail-lists-verification.json',historical_reports_note='Earlier dedicated reports are historical unless source hashes match. Current aggregate: detail-lists-checkpoint.json.')
n['next_implementation'][1]='Remaining state-selected targets/persona, below-defense selection, explicit lazy-target cache history; enemy identities in target lists and list/definition capacity expansion, then incoming/live-event semantics'
n['layout'].update(target_kind_17='eager ordered target list: q5 first inert descriptor row, q48 count',ordered_target_bits=64,ordered_target_capacity=21,NE_counts='source definitions plus inert target descriptor rows',workspace_bytes=208808)
n['new_characters']=checkpoint['new_characters']
n['completed_list_semantics']=['Nested friendly lists flattened in definition order on GPU; duplicates preserved, list rank children resolved eagerly','64-bit sequence carried through active instances, callbacks, scoped removal, named/stat notifications and heals; mask remains membership only','Duplicate HP posts, ammo changes and burst cooldown reductions; skill-clock reductions use a set and shields use unique dictionary recipients','Same recipient set with different order remains separate; identical plans share inert rows without splitting original trigger budgets or identities','CPU raw-rank ATK aggregation matches active-value and recipient-stack/caster arithmetic semantics','Adapter fixes CPU instant logger unhashable-list crash without vendor edits, target mutation or suppression of nested logs; compatibility file included in API cache fingerprint']
write('research/detail-expansion-next.json',n)
print(json.dumps({'passed':True,'list_cases':54,'catalog_cases':144,'python_tests':85,'compiled':72,'normal_api_total':api['total'],'objective_complete':False}))
