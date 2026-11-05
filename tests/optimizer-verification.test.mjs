import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import os from 'node:os';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {createEvaluator} from '../app/evaluation-queue.mjs';
import {isSampled,candidateKey,verifyOptimizer,pending,verificationView,verificationWorkers,displayedRows} from '../app/optimizer-verification.mjs';
import {run,view,workerTimeoutSeconds,cancelJob} from '../server.mjs';
const squad=i=>Array.from({length:5},(_,n)=>`${i}:${n}`);
const body=i=>({squad:squad(i),compute_backend:'native_detail',verify_detail:false});
const result=(b,damage=Number(b.squad[0].split(':')[0])+1,deferred=true)=>({members:b.squad.map(name=>({name})),total_damage:damage,compute:{backend:'native_detail',capture_id:b.squad[0],cpu_verification:deferred?{status:'pending'}:{matched:true,differing_fields:[]}}});
function job(count=20,id='unit3'){
 return {id,kind:'optimize',selectionBackend:'cpu',teamCount:1,groups:[],status:'running',index:count,cases:Array.from({length:count},(_,i)=>({evaluation:body(i),value:i})),results:Array.from({length:count},(_,i)=>({result:result(body(i)),value:i}))};
}
function fakeEvaluator({mismatch=()=>false,onVerify=()=>{}}={}){
 const calls=[];
 return {calls,async verify(rows,j){calls.push(...rows.map(r=>candidateKey(r.body)));await onVerify(rows,j);if(j.status==='cancelled')return;
  return rows.map(r=>{const bad=mismatch(r);const cpu=result(r.body,0,false);if(bad)cpu.compute={...cpu.compute,backend:'cpu',gpu_result_rejected:true,cpu_verification:{matched:false,differing_fields:['total_damage']}};
   if(bad)r.result=cpu;else r.result.compute.cpu_verification={matched:true,differing_fields:[]};return {matched:!bad,differing_fields:bad?['total_damage']:[],cpu_result:cpu};});
 }};
}

test('sha256 sampling is deterministic, candidate-order independent and exactly thresholded at 1/8',()=>{
 const expected=Array.from({length:100},(_,i)=>createHash('sha256').update('j'+candidateKey(body(i))).digest()[0]<32);
 assert.deepEqual(Array.from({length:100},(_,i)=>isSampled('j',candidateKey(body(i)))),expected);
 assert.deepEqual(Array.from({length:100},(_,i)=>99-i).map(i=>isSampled('j',candidateKey(body(i)))).reverse(),expected);
 assert.ok(expected.some(Boolean));assert.ok(expected.some(x=>!x));assert.notDeepEqual(expected,expected.map((_,i)=>isSampled('other',candidateKey(body(i)))));
});
test('at least one sample even when every successful candidate misses the hash threshold',async()=>{
 let id='';while(isSampled(id,candidateKey(body(0))))id+='x';
 const j=job(1,id),e=fakeEvaluator();await verifyOptimizer(j,e);
 assert.equal(e.calls.length,1);assert.equal(verificationView(j).sampled,1);assert.equal(j.results[0].result.compute.verification_kind,'sample');
});
test('displayed set includes every recommendation team; unshown candidates stay pending',async()=>{
 const j=job(60);j.teamCount=5;const e=fakeEvaluator();await verifyOptimizer(j,e);
 assert.equal(displayedRows(j).length,5);assert.ok(displayedRows(j).every(r=>!pending(r.result)));
 assert.ok(j.results.some(r=>pending(r.result)));assert.equal(verificationView(j).displayed,5);
 const keys=new Set(e.calls);for(const r of displayedRows(j))assert.ok(keys.has(JSON.stringify(r.result.members.map(m=>m.name))));
 assert.equal(view(j).recommendation.teams.length,5);
});
for(const mode of ['sample','displayed'])test(`${mode} mismatch escalates to all remaining candidates and recomputes recommendation`,async()=>{
 const j=job(32);let target;
 if(mode==='sample')target=j.cases.find(c=>isSampled(j.id,candidateKey(c.evaluation))).evaluation.squad[0];
 else {target=j.cases.at(-1).evaluation.squad[0];while(isSampled(j.id,candidateKey(j.cases.at(-1).evaluation)))j.id+='x';}
 const e=fakeEvaluator({mismatch:r=>r.body.squad[0]===target});await verifyOptimizer(j,e,{concurrency:3});
 assert.equal(e.calls.length,32);assert.equal(new Set(e.calls).size,32);
 assert.ok(j.results.every(r=>!pending(r.result)));assert.equal(j.verification.escalated,true);assert.equal(j.verification.mismatches,1);
 assert.ok(j.verification.reason);assert.equal(verificationView(j).verified,32);
 const bad=j.results.find(r=>r.result.compute.gpu_result_rejected);assert.equal(bad.result.total_damage,0);
 assert.notDeepEqual(j.incumbent.teams[0].squad,bad.result.members.map(m=>m.name));
 assert.equal(j.incumbent.damage,Math.max(...j.results.map(r=>r.result.total_damage)));
 assert.ok(displayedRows(j).every(r=>!pending(r.result)));
});
test('stale GPU incumbent scores are refreshed before selecting CPU-corrected recommendation',async()=>{
 const j=job(3);j.incumbent={damage:999999,teams:[{squad:squad(2),damage:999999}]};
 const e=fakeEvaluator({mismatch:r=>r.body.squad[0]==='2:0'});await verifyOptimizer(j,e);
 assert.equal(j.incumbent.damage,2);assert.deepEqual(j.incumbent.teams[0].squad,squad(1));
});
test('extend checks new displayed squads and retains sampling/escalation accounting',async()=>{
 const j=job(2),e=fakeEvaluator();await verifyOptimizer(j,e);const oldCalls=e.calls.length;
 j.cases.push({evaluation:body(99),value:99});j.results.push({result:result(body(99)),value:99});j.index++;
 await verifyOptimizer(j,e);assert.ok(e.calls.length>oldCalls);assert.deepEqual(j.incumbent.teams[0].squad,squad(99));assert.ok(!pending(j.results.at(-1).result));
 j.verification.escalated=true;j.cases.push({evaluation:body(100)});j.results.push({result:result(body(100))});await verifyOptimizer(j,e);
 assert.ok(j.results.every(r=>!pending(r.result)));
});
test('parallel verification obeys cpus-1 default and an explicit bound',async()=>{
 assert.equal(verificationWorkers(),Math.max(1,os.cpus().length-1));
 const j=job(24);j.verification={sampled:new Set(),displayed:new Set(),mismatches:0,escalated:true};let active=0,peak=0;
 const e=fakeEvaluator({onVerify:async()=>{active++;peak=Math.max(peak,active);await new Promise(r=>setTimeout(r,3));active--;}});
 await verifyOptimizer(j,e,{concurrency:3});assert.equal(peak,Math.min(3,verificationWorkers()));assert.equal(active,0);assert.equal(e.calls.length,24);
});
test('cancel during verification starts no further work and publishes no pending recommendation',async()=>{
 const j=job(40);j.verification={sampled:new Set(),displayed:new Set(),mismatches:0,escalated:true};
 const e=fakeEvaluator({onVerify:async(rows,j)=>{j.status='cancelled';await Promise.resolve();}});
 await verifyOptimizer(j,e,{concurrency:2});assert.ok(e.calls.length<=2);assert.equal(j.status,'cancelled');assert.ok(j.results.every(r=>pending(r.result)));assert.equal(view(j).recommendation,null);
});
test('view never exposes a pending or escalated-but-incomplete recommendation',()=>{
 const j=job(2);j.incumbent={damage:2,teams:[{squad:squad(1),damage:2}]};assert.equal(view(j).recommendation,null);
 j.results[1].result.compute.cpu_verification={matched:true};assert.ok(view(j).recommendation);
 j.verification={sampled:new Set(),displayed:new Set(),escalated:true};assert.equal(view(j).recommendation,null);
});
test('cache separates deferred and full, then verification upgrades the cached result',async()=>{
 const calls=[];const cache=new Map();
 const e=createEvaluator({cache,keyOf:JSON.stringify,worker:async r=>{calls.push(r);if(r.action==='verify_portable_detail')return r.evaluations.map(({body})=>({matched:true,differing_fields:[],cpu_result:result(body,1,false)}));return r.evaluations.map(b=>({result:result(b,1,r.verification==='deferred')}));}});
 const b=body(1),j={kind:'optimize',status:'running'};
 const deferred=await e.one(b,j);assert.ok(pending(deferred));assert.equal(calls[0].verification,'deferred');assert.equal(e.isCached(b),false);
 const full=await e.one(b);assert.ok(!pending(full));assert.equal(calls.length,2);assert.equal(calls[1].verification,undefined);
 assert.equal((await e.one(b,j)).cache_hit,true);
 const b2={...body(2),verification:'deferred',_verification:'deferred'};
 const row={body:b2,result:await e.one(b2,j)};await e.verify([row],j);
 assert.equal(calls.at(-1).action,'verify_portable_detail');assert.equal(calls.at(-1).evaluations[0].body.verification,undefined);
 const after=await e.one(b2);assert.equal(after.cache_hit,true);assert.ok(after.compute.cpu_verification.matched);assert.equal(calls.length,4);
});
test('cache stores authoritative CPU rejection after mismatch',async()=>{
 const b=body(1),cpu={...result(b,1,false),compute:{backend:'cpu',gpu_result_rejected:true,cpu_verification:{matched:false,differing_fields:['total_damage']}}};
 const e=createEvaluator({keyOf:JSON.stringify,worker:async r=>r.action==='verify_portable_detail'?[{matched:false,differing_fields:['total_damage'],cpu_result:cpu}]:[{result:result(b,999,true)}]});
 const j={kind:'optimize',status:'running'},row={body:b,result:await e.one(b,j)};await e.verify([row],j);
 assert.equal(row.result.total_damage,1);assert.ok(row.result.compute.gpu_result_rejected);assert.equal((await e.one(b)).total_damage,1);
});
for(const kind of ['compare','board','batch','search',undefined])test(`${kind||'direct'} requests remain full even with an HTTP verification field`,async()=>{
 const requests=[],b={...body(1),verification:'deferred',_verification:'deferred'};
 const e=createEvaluator({keyOf:JSON.stringify,worker:async r=>{requests.push(r);return [{result:result(b,1,false)}];}});
 await e.one(b,kind?{kind}:undefined);assert.equal(requests[0].verification,undefined);assert.equal(requests[0].evaluations[0].verification,undefined);assert.equal(requests[0].evaluations[0]._verification,undefined);
});
test('browser prepare and finish both carry deferred option only for optimizer jobs',async()=>{
 const calls=[],b={...body(1),compute_backend:'browser_detail'};
 const j={kind:'optimize',status:'running',browser:{request:async wires=>wires.map(()=>({upload:true}))}};
 const e=createEvaluator({keyOf:JSON.stringify,worker:async r=>{calls.push(r);return r.action==='prepare_browser_wires'?[{wire:{}}]:[{result:result(b)}];}});
 await e.one(b,j);assert.deepEqual(calls.map(c=>[c.action,c.verification]),[['prepare_browser_wires','deferred'],['finish_browser','deferred']]);
});
test('run pauses with a verified recommendation, resumes pending candidates and completes',async()=>{
 const j=job(4);j.index=0;j.results=[];let pause=true;
 const e=createEvaluator({keyOf:JSON.stringify,worker:async r=>{
  if(r.action==='verify_portable_detail')return r.evaluations.map(({body})=>({matched:true,differing_fields:[],cpu_result:result(body,1,false)}));
  if(pause){j.pauseRequested=true;pause=false;}return r.evaluations.map(b=>({result:result(b)}));
 }});
 await run(j,{evaluator:e});assert.equal(j.status,'paused');assert.equal(j.index,1);assert.ok(view(j).recommendation);assert.ok(displayedRows(j).every(r=>!pending(r.result)));
 j.pauseRequested=false;await run(j,{evaluator:e});assert.equal(j.status,'complete');assert.equal(j.index,4);assert.ok(view(j).recommendation);
});
for(const selectionBackend of ['metal','cuda'])test(`${selectionBackend} selection is verified after its GPU selection stage`,async()=>{
 const j=job(4);j.index=0;j.results=[];j.selectionBackend=selectionBackend;j.prefilterAttempted=true;const calls=[];
 const worker=async r=>{calls.push(r.action);if(r.action==='select')return {recommendation:{damage:4,teams:[{squad:squad(3),damage:4}]}};if(r.action==='verify_portable_detail')return r.evaluations.map(({body})=>({matched:true,differing_fields:[],cpu_result:result(body,1,false)}));return r.evaluations.map(b=>({result:result(b)}));};
 const e=createEvaluator({keyOf:JSON.stringify,worker});await run(j,{worker,evaluator:e});
 assert.equal(j.status,'complete');assert.ok(calls.indexOf('verify_portable_detail')>calls.indexOf('select'));assert.ok(view(j).recommendation);assert.ok(displayedRows(j).every(r=>!pending(r.result)));
});
test('verification process routing, timeout and cancellation include every parallel child',()=>{
 const source=readFileSync(new URL('../server.mjs',import.meta.url),'utf8');
 assert.match(source,/const script=\[.*'verify_portable_detail'.*\?'app\/portable_detail_service.py'/);
 const kills=[0,0,0];const children=kills.map((_,i)=>({kill(){kills[i]++;}}));
 const j={status:'running',children:new Set(children),child:children[2]};cancelJob(j);assert.equal(j.status,'cancelled');assert.deepEqual(kills,[1,1,1]);
 assert.equal(workerTimeoutSeconds({action:'verify_portable_detail',evaluations:[{}]}),120);
});
test('UI labels cover verified, sample and pending; recommendation panels state policy and escalation',()=>{
 const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8');const helper=source.split('\n').find(l=>l.startsWith('function verificationLabel('));
 for(const [compute,expected] of [[{cpu_verification:{matched:true}},'CPU照合済み'],[{verification_kind:'sample'},'抜き取り照合済み'],[{cpu_verification:{status:'pending'}},'未照合（候補の順位付けのみ）']])assert.equal(runInNewContext(helper+'\nverificationLabel({compute})',{compute}),expected);
 const rec=source.split('\n').find(l=>l.startsWith('function recommendationHTML('));assert.match(rec,/表示する全部隊と候補の1\/8/);assert.match(rec,/job.verification\?\.escalated/);assert.match(rec,/verificationLabel/);
});

test('cached CPU rejection escalates every pending candidate in the new job',async()=>{
 const j=job(16);j.results[0].result.compute={backend:'cpu',gpu_result_rejected:true,cpu_verification:{matched:false}};
 const e=fakeEvaluator();await verifyOptimizer(j,e);assert.equal(j.verification.escalated,true);assert.equal(j.verification.mismatches,1);assert.ok(j.results.every(r=>!pending(r.result)));
});

test('pause requested during verification finishes the required display checks before pausing',async()=>{
 const j=job(8);j.index=0;j.results=[];
 const e=createEvaluator({keyOf:JSON.stringify,worker:async r=>{
  if(r.action==='verify_portable_detail'){j.pauseRequested=true;assert.equal(j.phase,'表示する部隊をCPUで照合中');return r.evaluations.map(({body})=>({matched:true,differing_fields:[],cpu_result:result(body,1,false)}));}
  return r.evaluations.map(b=>({result:result(b)}));
 }});
 await run(j,{evaluator:e});assert.equal(j.status,'paused');assert.ok(view(j).recommendation);assert.ok(displayedRows(j).every(r=>!pending(r.result)));
});
test('cancelled verification response cannot upgrade the cache or publish the CPU result',async()=>{
 const j={kind:'optimize',status:'running'},b=body(1);let finish;
 const e=createEvaluator({keyOf:JSON.stringify,worker:async r=>{
  if(r.action==='verify_portable_detail'){await new Promise(resolve=>finish=resolve);return [{matched:true,differing_fields:[],cpu_result:result(b,1,false)}];}
  return [{result:result(b)}];
 }});
 const row={body:b,result:await e.one(b,j)},checking=e.verify([row],j);cancelJob(j);finish();await checking;
 assert.ok(pending(row.result));assert.equal(e.isCached(b),false);
});
test('verification failure fails the job and hides its pending recommendation',async()=>{
 const j=job(3);j.index=0;j.results=[];
 const e=createEvaluator({keyOf:JSON.stringify,worker:async r=>{if(r.action==='verify_portable_detail')throw Error('fresh CPU failed');return r.evaluations.map(b=>({result:result(b)}));}});
 await run(j,{evaluator:e});assert.equal(j.status,'failed');assert.match(j.error,/fresh CPU failed/);assert.equal(view(j).recommendation,null);
});
