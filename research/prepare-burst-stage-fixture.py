import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import engine_worker as a
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def write(p,r):(ROOT/p).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
before=read('research/detail-coverage-burst-gauge.json');after=read('research/detail-coverage-burst-stage.json')
was={r['character'] for r in before['results'] if r['supported']}
added=[r['character'] for r in after['results'] if r['supported'] and r['character'] not in was]
body=read('research/detail-burst-gauge-api-fixture.json');old=body['squad'][0];who=added[0]
body['squad'][0]=who;body['profile']['chars'][who]=body['profile']['chars'].pop(old)
for k in ['patches','stat_deltas']:
 if old in body.get(k,{}):body[k][who]=body[k].pop(old)
compiled=a.evaluate({**body,'_compile_gpu_detail':True})
write('research/detail-burst-stage-api-fixture.json',body)
print(json.dumps({'new_characters':added,'rows':len(compiled['program']['effects'])},ensure_ascii=True))
n=read('research/detail-expansion-next.json')
n['current_work']={'feature':'v18 variable burst stages and reentry','abi':'detail_burst_stage_v18','objective_complete':False,'compile_coverage':113,'new_characters':added,'synthetic_cases_per_backend':50,'real_cases_per_backend':6,'cpu_reference_cases':25,'cpu_reference_report':'research/detail-burst-stage-cpu-references.json','ptx_build':'completed','native_build_session':23700,'verification_status':'not run yet; wait for native build, then run scripts/verify-burst-stage-detail.py','api_fixture':'research/detail-burst-stage-api-fixture.json','api_status':'compiled only; smoke pending','notes':'v17 checkpoint is historical after v18 code changes. No full v18 regression run yet. Native compile and host/CUDA source are frozen.'}
n['checkpoint']['python_test_scope']='Historical v17: 110 tests in 1089.902 seconds; no skips'
write('research/detail-expansion-next.json',n)
