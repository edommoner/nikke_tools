/** Local end-to-end routing and cache isolation for the detailed backend. */
import {spawn} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {once} from 'node:events';
import assert from 'node:assert/strict';
const port=4333,url=`http://127.0.0.1:${port}`,delay=ms=>new Promise(r=>setTimeout(r,ms));
const child=spawn(process.execPath,['server.mjs'],{env:{...process.env,PORT:String(port)},windowsHide:true,stdio:['ignore','pipe','pipe']});
let err='';child.stderr.on('data',b=>err+=b);
async function api(route,body){const res=await fetch(url+route,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const result=await res.json();assert.ok(res.ok,JSON.stringify(result));return result;}
async function job(body){let j=await api('/api/jobs',body);for(let i=0;i<1000;i++){j=await api(`/api/jobs/${j.id}`);if(j.status==='complete')return j;if(j.status==='failed')throw Error(j.error);await delay(100);}throw Error('timeout');}
try{
 await once(child.stdout,'data');
 const demoMode=process.argv[2]==='--gpu-demo';
 const data=demoMode?await api('/api/demo?gpu_detail=true'):null;
 const evaluation=demoMode?{profile:data.profile,squad:data.squad,duration:60,level:400,enemy:{def:31784,code:'풍압',core_px:0,distance:30},burst_policy:'mast3',compute_backend:'cuda_detail',verify_detail:true}:JSON.parse(readFileSync(process.argv[2]||'research/detail-api-fixture.json','utf8'));
 const g=await job({kind:'compare',evaluation});assert.equal(g.results.length,2);
 for(const row of g.results){assert.equal(row.result.compute.backend,'cuda_detail');assert.equal(row.result.compute.cpu_verification.matched,true);assert.equal(row.result.shooting_policy,evaluation.shooting_policy||'auto');assert.equal(row.result.burst_gauge_mode,evaluation.burst_gauge_mode||'fixed');}
 for(const row of g.results){assert.ok(row.result.boss_timeline.length>0);assert.equal(row.result.compute.cpu_verification.boss_timeline_equal,true);}
 const c=await job({kind:'compare',evaluation:{...evaluation,compute_backend:'cpu'}});
 assert.equal(c.results[1].result.compute.backend,'cpu');assert.equal(c.results[1].result.total_damage,g.results[1].result.total_damage);assert.equal(c.results[1].result.cache_hit,false);
 let shootingModesSeparate=false;
 if(evaluation.shooting_policy==='character'){
  const automatic=await job({kind:'compare',evaluation:{...evaluation,shooting_policy:'auto'}});
  for(const row of automatic.results){assert.equal(row.result.compute.backend,'cuda_detail');assert.equal(row.result.compute.cpu_verification.matched,true);assert.equal(row.result.shooting_policy,'auto');}
  assert.equal(automatic.results[1].result.cache_hit,false);shootingModesSeparate=true;
 }
 let gaugeModesSeparate=false;
 if(evaluation.burst_gauge_mode==='accumulate'){
  const fixed=await job({kind:'compare',evaluation:{...evaluation,burst_gauge_mode:'fixed'}});
  for(const row of fixed.results){assert.equal(row.result.compute.backend,'cuda_detail');assert.equal(row.result.compute.cpu_verification.matched,true);assert.equal(row.result.burst_gauge_mode,'fixed');}
  assert.equal(fixed.results[1].result.cache_hit,false);gaugeModesSeparate=true;
 }
 const alternateSeed=(evaluation.seed??0)===0?12345:0;
 const seeded=await job({kind:'compare',evaluation:{...evaluation,seed:alternateSeed}});
 for(const row of seeded.results){assert.equal(row.result.seed,alternateSeed);assert.equal(row.result.compute.backend,'cuda_detail');assert.equal(row.result.compute.cpu_verification.matched,true);assert.equal(row.result.compute.cpu_verification.seed_equal,true);}
 assert.equal(seeded.results[1].result.cache_hit,false);
 let coreModesSeparate=false;
 if(process.argv.includes('--core-presence')){
  assert.ok(evaluation.enemy.core_px>=1,'Core-presence check starts with an enabled core');
  const noCore=await job({kind:'compare',evaluation:{...evaluation,enemy:{...evaluation.enemy,core_px:0}}});
  for(const row of noCore.results){assert.equal(row.result.compute.backend,'cuda_detail');assert.equal(row.result.compute.cpu_verification.matched,true);}
  assert.equal(noCore.results[1].result.cache_hit,false);coreModesSeparate=true;
 }
 let partsCacheSeparate=false;
 if(process.argv.includes('--parts')){
  assert.ok(evaluation.enemy.parts?.length,'Parts check requires authored parts');
  assert.ok(g.results[1].result.parts_state.some(p=>p.damage>0));
  assert.equal(g.results[1].result.compute.cpu_verification.parts_state_equal,true);
  const noParts=await job({kind:'compare',evaluation:{...evaluation,enemy:{...evaluation.enemy,parts:[]}}});
  for(const row of noParts.results){assert.equal(row.result.compute.backend,'cuda_detail');assert.equal(row.result.compute.cpu_verification.matched,true);assert.equal(row.result.parts_state,undefined);}
  assert.equal(noParts.results[1].result.cache_hit,false);assert.ok(g.results[1].result.total_damage>noParts.results[1].result.total_damage);partsCacheSeparate=true;
 }
 const board=await job({kind:'board',teams:[{index:0,evaluation}]});assert.equal(board.results[0].result.compute.backend,'cuda_detail');assert.equal(board.results[0].result.total_damage,g.results[1].result.total_damage);
 const unsupportedEnemy={...evaluation.enemy,patterns:[{id:'armor',kind:'vanish'}]};
 const unsupportedWorld=await job({kind:'compare',evaluation:{...evaluation,enemy:unsupportedEnemy}});
 const worldCpu=await job({kind:'compare',evaluation:{...evaluation,enemy:unsupportedEnemy,compute_backend:'cpu'}});
 for(let i=0;i<2;i++){assert.equal(unsupportedWorld.results[i].result.compute.backend,'cpu');assert.ok(unsupportedWorld.results[i].result.compute.unsupported.length);assert.equal(unsupportedWorld.results[i].result.total_damage,worldCpu.results[i].result.total_damage);}
 const demo=await api('/api/demo');const fallback=await job({kind:'compare',evaluation:{...evaluation,profile:demo.profile,squad:demo.squad,patches:{},stat_deltas:{}}});
 assert.equal(fallback.results[1].result.compute.backend,'cpu');assert.ok(fallback.results[1].result.compute.unsupported.length);
 const report={generated_at:new Date().toISOString(),passed:true,normal_compare_gpu:true,cpu_verification:true,board_gpu:true,cache_separated:true,unsupported_cpu_fallback:true,total:g.results[1].result.total_damage};
 report.burst_gauge_mode=evaluation.burst_gauge_mode||'fixed';report.gauge_modes_separate=gaugeModesSeparate;
 report.seed=evaluation.seed??0;report.seed_cache_separated=true;
 report.shooting_policy=evaluation.shooting_policy||'auto';report.shooting_modes_separate=shootingModesSeparate;
 report.core_modes_separate=coreModesSeparate;
 report.compute=g.results[1].result.compute;
 report.parts_cache_separate=partsCacheSeparate;
 if(evaluation.enemy.parts?.length)report.parts_state=g.results[1].result.parts_state;
 report.request_sha256=createHash('sha256').update(JSON.stringify(evaluation)).digest('hex');
 report.source_sha256=Object.fromEntries(['app/detail_gpu.py','app/detail_world.py','app/gpu_combat.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/engine_compat.py','app/gpu_service.py','server.mjs','web/app.js','web/parts-model.mjs','web/roster-model.mjs','web/index.html','scripts/smoke-detail-boss-buffs.mjs','app/detail_boss.py','web/phase-model.mjs',...(!demoMode&&process.argv[2]?[process.argv[2]]:[])].map(p=>[p,createHash('sha256').update(readFileSync(p)).digest('hex')]));
 if(demoMode)writeFileSync('research/detail-gpu-demo-api-verification.json',JSON.stringify(report,null,2)+'\n');
 report.boss_timeline=g.results[1].result.boss_timeline;report.patterns_verified=true;report.unsupported_boss_cpu_parity=true;writeFileSync('research/detail-boss-buffs-api-verification.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}catch(e){console.error(e,err);process.exitCode=1;}
finally{child.kill();await once(child,'exit');}
