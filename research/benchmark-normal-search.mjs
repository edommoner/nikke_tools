/** Real normal-path search latency; unique inputs avoid result-cache speedups. */
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import assert from 'node:assert/strict';
const [output,portText='4345',baselinePath,fixture='research/base-copy-api-fixtures.json']=process.argv.slice(2),port=Number(portText);
assert.ok(output&&Number.isInteger(port));
const files=['server.mjs','app/detail_gpu.py','app/gpu_service.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json',fixture,'research/benchmark-normal-search.mjs'];
const hashes=()=>Object.fromEntries(files.map(p=>[p,createHash('sha256').update(readFileSync(p)).digest('hex')]));
const source_sha256=hashes();
const loaded=JSON.parse(readFileSync(fixture,'utf8'));
const evaluation=structuredClone(Array.isArray(loaded)?loaded.find(r=>r.name==='raw-copy-combined').evaluation:loaded);
evaluation.compute_backend='cuda_detail';evaluation.verify_detail=false;evaluation.seed=12345;
async function api(route,body){
 const response=await fetch(`http://127.0.0.1:${port}${route}`,body?{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}:{});
 const result=await response.json();assert.ok(response.ok,JSON.stringify(result));return result;
}
async function search(min,max){
 const started=performance.now();
 let job=await api('/api/jobs',{kind:'search',evaluation,target:1,variable:{character:evaluation.squad[0],kind:'atk',min,max,step:1000}});
 for(let i=0;i<6000;i++){
  job=await api('/api/jobs/'+job.id);assert.notEqual(job.status,'failed',job.error);
  if(job.status==='complete')return {job,wall_ms:performance.now()-started};
  await new Promise(resolve=>setTimeout(resolve,50));
 }
 throw Error('Normal search benchmark timeout');
}
await search(0,0); // Warm context/module; measured candidates use different values.
const {job,wall_ms}=await search(1000,8000);
assert.equal(job.results.length,8);assert.equal(job.index,8);
for(const item of job.results){assert.ok(item.result);assert.equal(item.result.compute.backend,'cuda_detail');assert.equal(item.result.cache_hit,false);}
const semantic=result=>Object.fromEntries(['total_damage','members','base_stats','burst_timeline','seed','burst_policy','shooting_policy','burst_gauge_mode','parts_state','boss_timeline','incoming_hits'].map(key=>[key,result[key]??null]));
const results=job.results.map(r=>({value:r.value,meets:r.meets,result:semantic(r.result),compute:r.result.compute}));
let speedup;
if(baselinePath&&baselinePath!=='-'){
 const baseline=JSON.parse(readFileSync(baselinePath,'utf8'));assert.ok(baseline.passed);
 assert.deepEqual(results.map(({compute,...r})=>r),baseline.results.map(({compute,...r})=>r));
 speedup=baseline.wall_ms/wall_ms;
}
assert.deepEqual(hashes(),source_sha256);
writeFileSync(output,JSON.stringify({passed:true,port,wall_ms,normal_api:true,candidates:8,cache_hits:0,baseline:baselinePath&&baselinePath!=='-'?baselinePath:null,speedup,results,source_sha256},null,2)+'\n');
console.log(JSON.stringify({passed:true,candidates:8,wall_ms,speedup,batch_sizes:results.map(r=>r.compute.batch_size||1)}));
