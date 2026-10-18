import copy,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker as a
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
body=read('research/detail-cleanse-api-fixture.json');old=body['squad'][0];who='코코아'
body['squad'][0]=who;body['profile']['chars'][who]=body['profile']['chars'].pop(old)
for k in ('patches','stat_deltas'):
 if old in body.get(k,{}):body[k][who]=body[k].pop(old)
body.update(seed=12345)
compiled=a.evaluate({**body,'_compile_gpu_detail':True});write('research/detail-random-api-fixture.json',body)
def rename(v):
 if isinstance(v,dict):return {(who if k==old else k):rename(x) for k,x in v.items()}
 if isinstance(v,list):return [rename(x) for x in v]
 return who if v==old else v
ui=rename(read('research/detail-cleanse-ui-fixture.json'));ui['snapshot']['snapshot_id']='synthetic-random-v20';ui.setdefault('settings',{})['random-seed']=12345;write('research/detail-random-ui-fixture.json',ui)
n=read('research/detail-expansion-next.json');n['generated_at']=datetime.now(timezone.utc).isoformat()
n['current_work']=dict(feature='v20 seeded random targets',abi='detail_random_v20',objective_complete=False,compile_coverage=117,favorite_contexts_compiled=459,new_characters=[who],status='kernel implemented; diagnostic revealed expiration PRNG discrepancy, repaired and rebuilding; full validation pending',
 seed_contract='uint32, default0 shared by CPU/GPU; request, save/restore, result and comparison identities',random_cache_entries=1024,cache_overflow='reject whole GPU result; CPU fallback',effect_row_width=264,
 historical_checkpoint='research/detail-cleanse-checkpoint.json',notes='V19 checkpoint full114 passed. Current v20 parity not yet proven. Never kill user4317. Owned4332 server83134 still caches v19 host; restart before v20 UI. Raw Cocoa positive injection, full117 regression, native/PTX, API/UI required before checkpoint.')
n['next_action']={'feature':'Finish v20 seeded target parity and normal API/UI','no_live_verification_jobs':False}
write('research/detail-expansion-next.json',n)
print(json.dumps({'api_rows':len(compiled['program']['effects']),'seed':body['seed'],'abi':'detail_random_v20'}))
