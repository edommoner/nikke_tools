import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import engine_worker as a
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
before=read('research/detail-coverage-burst-stage.json');after=read('research/detail-coverage-cleanse.json')
was={r['character'] for r in before['results'] if r['supported']};added=[r['character'] for r in after['results'] if r['supported'] and r['character'] not in was]
body=read('research/detail-burst-stage-api-fixture.json');old=body['squad'][0];who=added[0]
body['squad'][0]=who;body['profile']['chars'][who]=body['profile']['chars'].pop(old)
for k in ['patches','stat_deltas']:
 if old in body.get(k,{}):body[k][who]=body[k].pop(old)
compiled=a.evaluate({**body,'_compile_gpu_detail':True});write('research/detail-cleanse-api-fixture.json',body)
def rename(v):
 if isinstance(v,dict):return {(who if k==old else k):rename(x) for k,x in v.items()}
 if isinstance(v,list):return [rename(x) for x in v]
 return who if v==old else v
ui=rename(read('research/detail-burst-stage-ui-fixture.json'));ui['snapshot']['snapshot_id']='synthetic-cleanse-v19';write('research/detail-cleanse-ui-fixture.json',ui)
n=read('research/detail-expansion-next.json');n['generated_at']=datetime.now(timezone.utc).isoformat();n['objective_complete']=False
n['current_work']=dict(feature='v19 per-recipient debuff cleanse',abi='detail_cleanse_v19',objective_complete=False,compile_coverage=116,favorite_contexts_compiled=455,new_characters=added,
 ptx_build_session=38869,native_build_session=39206,build_status='both terminal0; current CU frozen',
 compiler_test_status='passed one limit-validation test',focused_session=83032,focused_status='terminal0: 5 tests passed (periodic, typed damage, instances)',
 formal_session=5569,formal_status='terminal0: native52 plus PTX52 passed104',formal_report='research/detail-cleanse-verification.json',
 nested_session=9078,nested_log='research/detail-cleanse-nested-verification.log',nested_report='research/detail-cleanse-nested-verification.json',nested_status='native8 passed including final health; PTX8 running',
 regression_session=8391,regression_log='research/detail-cleanse-tests.log',expected_test_count=114,regression_status='running',
 api_fixture='research/detail-cleanse-api-fixture.json',api_fixture_rows=len(compiled['program']['effects']),api_status='compiled; smoke pending, wait for a GPU slot',
 ui_fixture='research/detail-cleanse-ui-fixture.json',ui_status='not tested yet; owned4332 server18091 cached v18 host, restart only4332 after proof; never user4317',
 semantics='Oldest harmful only, per-recipient limits and atomic partial strips; no end notifications or timer cancellation. Preserve shield/bullet maps; stripped scaling DoT falls back to live reference.',
 random_status='Standalone PRNG verified but not combat-integrated; Cocoa remains rejected for random harmful target. Do not claim RNG integration.',
 notes='Poll exact live9078/8391; main5569 and focused83032 terminal0. No edits to CUDA/compiler/current verifiers while they run. V18 checkpoint is historical after v19 source edits. Crust positive tests use authored tap and hold controls; full raw character effects retained. All-character goal remains active.')
n['current_work']['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-build.json','app/detail_effects-sm86.json','scripts/verify-cleanse-detail.py','scripts/verify-cleanse-nested.py']}
n['next_action']={'feature':'Finish v19 evidence, then integrate seeded GPU random targets and exact lazy target cache','no_live_verification_jobs':False,'notes':'Use current_work live handles; do not rerun obsolete v18 checkpoint/progress writers.'}
write('research/detail-expansion-next.json',n)
print(json.dumps({'new_characters':added,'api_rows':len(compiled['program']['effects']),'formal_passed':104},ensure_ascii=True))
