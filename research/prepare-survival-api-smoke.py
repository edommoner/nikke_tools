"""Adapt the ordinary end-to-end test without overwriting v33 evidence."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/smoke-detail-incoming.mjs').read_text(encoding='utf-8')
s=s.replace('const port=4333,','const port=4334,')
s=s.replace('research/detail-api-fixture.json','research/detail-survival-api-fixture.json')
s=s.replace('research/detail-incoming-api-verification.json','research/detail-survival-api-verification.json')
s=s.replace('scripts/smoke-detail-incoming.mjs','scripts/smoke-detail-survival.mjs')
s=s.replace("'app/engine_compat.py',","'app/engine_compat.py','app/survival_compat.py',")
needle=" const c=await job({kind:'compare',evaluation:{...evaluation,compute_backend:'cpu'}});"
assert needle in s
s=s.replace(needle," for(const row of g.results){assert.ok(row.result.incoming_hits.some(h=>h.down));assert.equal(row.result._down_mask,0);assert.ok(row.result.compute.final_hp['앨리스'].hp>0);}\n"+needle)
needle=" const unsupportedEnemy="
assert needle in s
s=s.replace(needle," const pureGpu=await job({kind:'compare',evaluation:{...evaluation,verify_detail:false}});\n for(let i=0;i<2;i++){assert.equal(pureGpu.results[i].result.compute.backend,'cuda_detail');assert.equal(pureGpu.results[i].result.compute.cpu_verification,undefined);assert.equal(pureGpu.results[i].result.total_damage,g.results[i].result.total_damage);assert.equal(pureGpu.results[i].result.cache_hit,false);}\n"+needle)
s=s.replace('cpu_verification:true,board_gpu:true','cpu_verification:true,pure_gpu_path_verified:true,board_gpu:true')
(ROOT/'scripts/smoke-detail-survival.mjs').write_text(s,encoding='utf-8')
print('Prepared ordinary API survival test on isolated port 4334.')
