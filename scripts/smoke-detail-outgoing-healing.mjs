/** Ordinary actual-healer owned growth and Healing cube with complete raw skills. */
import {spawn} from 'node:child_process';
import {readFileSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {once} from 'node:events';
import assert from 'node:assert/strict';
const port=4335, url=`http://127.0.0.1:${port}`, delay=ms=>new Promise(r=>setTimeout(r,ms));
const child=spawn(process.execPath,['server.mjs'],{env:{...process.env,PORT:String(port)},windowsHide:true,stdio:['ignore','pipe','pipe']});
let errors='';child.stderr.on('data',data=>errors+=data);
async function api(route,body){
 const res=await fetch(url+route,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
 const result=await res.json();assert.ok(res.ok,JSON.stringify(result));return result;
}
async function job(body){
 let j=await api('/api/jobs',body);
 for(let i=0;i<1800;i++){
  j=await api(`/api/jobs/${j.id}`);
  if(j.status==='complete')return j;
  if(j.status==='failed')throw Error(j.error);
  await delay(100);
 }
 throw Error('Local HP-edge job timed out');
}
try{
 await once(child.stdout,'data');
 const fixture='research/detail-outgoing-healing-api-fixture.json';
 const evaluation=JSON.parse(readFileSync(fixture,'utf8'));
 const files=['scripts/smoke-detail-outgoing-healing.mjs',fixture,'app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/gpu_service.py','app/gpu_combat.py','app/detail_world.py','app/detail_boss.py','server.mjs','web/index.html','web/app.js','web/board-model.mjs'];
 const hashes=()=>Object.fromEntries(files.map(path=>[path,createHash('sha256').update(readFileSync(path)).digest('hex')]));
 const source_sha256=hashes();assert.equal(JSON.parse(readFileSync('app/detail_effects-build.json','utf8')).abi,'detail_outgoing_healing_v39');
 const verified=await job({kind:'compare',evaluation});assert.equal(verified.results.length,2);
 for(const {result} of verified.results){
  assert.equal(result.compute.backend,'cuda_detail');assert.equal(result.compute.cpu_verification.matched,true);
  assert.equal(result.compute.workspace_bytes,1074184);
  assert.ok(Number.isFinite(result.compute.final_hp['프리카'].hp_pct));
 }
 // Target ranking and HP-dependent actions can make squad damage nonmonotonic.
 // Check the requested base-stat edits directly, plus independent CPU parity.
 for(const [stat,amount] of Object.entries(evaluation.stat_deltas['프리카']))assert.equal(verified.results[1].result.base_stats['프리카'][stat]-verified.results[0].result.base_stats['프리카'][stat],amount);
 assert.notEqual(verified.results[1].result.total_damage,verified.results[0].result.total_damage);
 const cpu=await job({kind:'compare',evaluation:{...evaluation,compute_backend:'cpu'}});
 for(let i=0;i<2;i++){assert.equal(cpu.results[i].result.compute.backend,'cpu');assert.equal(cpu.results[i].result.total_damage,verified.results[i].result.total_damage);}
 const pure=await job({kind:'compare',evaluation:{...evaluation,verify_detail:false}});
 for(let i=0;i<2;i++){
  assert.equal(pure.results[i].result.compute.backend,'cuda_detail');
  assert.equal(pure.results[i].result.compute.cpu_verification,undefined);
  assert.equal(pure.results[i].result.total_damage,verified.results[i].result.total_damage);
  assert.equal(pure.results[i].result.cache_hit,false);
 }
 const board=await job({kind:'board',teams:[{index:0,evaluation}]});
 assert.equal(board.results[0].result.compute.backend,'cuda_detail');assert.equal(board.results[0].result.total_damage,verified.results[1].result.total_damage);
 const alternateSeed=await job({kind:'compare',evaluation:{...evaluation,seed:7654321}});
 for(const {result} of alternateSeed.results){assert.equal(result.compute.backend,'cuda_detail');assert.equal(result.compute.cpu_verification.matched,true);assert.equal(result.cache_hit,false);}
 const repeat=await job({kind:'compare',evaluation});assert.equal(repeat.results[1].result.cache_hit,true);
 assert.deepEqual(hashes(),source_sha256,'Sources changed during API acceptance');
 const result=verified.results[1].result;
 const report={generated_at:new Date().toISOString(),passed:true,objective_complete:false,abi:'detail_outgoing_healing_v39',normal_compare_gpu:true,pure_gpu_path_verified:true,cpu_verification:true,board_gpu:true,seed_cache_separated:true,cache_hit_verified:true,fictional_owned_data:true,live_account_import_verified:false,original_total:verified.results[0].result.total_damage,total:result.total_damage,delta:result.total_damage-verified.results[0].result.total_damage,original_base_stats:verified.results[0].result.base_stats,base_stats:result.base_stats,members:result.members,final_hp:result.compute.final_hp,compute:result.compute,source_sha256};
 writeFileSync('research/detail-outgoing-healing-api-verification.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({passed:true,total:report.total,delta:report.delta,pure_gpu_path_verified:true}));
}finally{
 if(child.exitCode===null){child.kill();await once(child,'exit');}
 if(errors)console.error(errors);
}
