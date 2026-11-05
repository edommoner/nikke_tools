import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import {advanceCases,createEvaluator,nativeBatchWorkers} from '../app/evaluation-queue.mjs';
import {cancelJob,run,view} from '../server.mjs';
import {ownNativeProcessGroup} from '../app/native-worker-process.mjs';
const deferred=()=>{let resolve,reject;const promise=new Promise((r,j)=>{resolve=r;reject=j;});return {promise,resolve,reject};};
const job=(n=160,kind='optimize',backend='native_detail')=>({kind,index:0,status:'running',results:[],cases:Array.from({length:n},(_,id)=>({value:id,evaluation:{id,compute_backend:backend}}))});
const rows=items=>items.map(b=>({result:{total_damage:b.id}}));
const tick=()=>new Promise(r=>setImmediate(r));

test('worker bound uses one batch per CPU',()=>{
 assert.deepEqual([1,2,3,5,6,9,12,128].map(nativeBatchWorkers),[1,2,3,5,6,9,12,128]);
});

test('native optimize waves overlap and publish in candidate order despite reverse completion',async()=>{
 const original=os.cpus;os.cpus=()=>Array(12).fill({});
 try{
  const j=job(),calls=[],waits=[];let active=0,peak=0;
  const evaluator={isCached:()=>false,many:async(items,job,options)=>{calls.push({items,options});active++;peak=Math.max(peak,active);const w=deferred();waits.push(w);await w.promise;active--;return rows(items);}};
  const running=advanceCases(j,evaluator);await tick();assert.equal(calls.length,10);assert.equal(j.index,0);
  assert.deepEqual(calls.map(c=>c.options.hostThreads),Array(10).fill(12));
  for(let i=9;i>=0;i--)waits[i].resolve();await running;
  assert.equal(peak,10);assert.equal(j.index,160);assert.deepEqual(j.results.map(r=>r.value),Array.from({length:160},(_,i)=>i));
 }finally{os.cpus=original;}
});

test('pause waits for all in-flight rows, resumes without replay, then extends in order',async()=>{
 const original=os.cpus;os.cpus=()=>Array(9).fill({});
 try{
  const j=job(96),waits=[];let calls=0;
  const evaluator={isCached:()=>false,many:async items=>{calls++;const w=deferred();waits.push(w);await w.promise;return rows(items);}};
  const running=advanceCases(j,evaluator);j.pauseRequested=true;waits[0].resolve();await tick();assert.equal(j.status,'running');assert.equal(j.index,0);
  for(let i=5;i>=1;i--)waits[i].resolve();await running;
  assert.equal(j.status,'paused');assert.equal(j.index,1);assert.equal(j.pendingGpuResults.rows.length,95);
  j.pauseRequested=false;j.status='running';await advanceCases(j,evaluator);assert.equal(calls,6);assert.equal(j.index,96);
  j.cases.push({value:96,evaluation:{id:96,compute_backend:'native_detail'}});
  const extending=advanceCases(j,evaluator);waits[6].resolve();await extending;assert.equal(j.index,97);
  assert.deepEqual(j.results.map(r=>r.value),Array.from({length:97},(_,i)=>i));
 }finally{os.cpus=original;}
});

test('cancel kills every concurrent child, drains batches and publishes/cache-saves nothing',async()=>{
 const original=os.cpus;os.cpus=()=>Array(12).fill({});
 try{
  const j=job(128),cache=new Map(),waits=[],killed=[];
  const evaluator=createEvaluator({cache,keyOf:JSON.stringify,worker:async(body,j)=>{
   const id=waits.length,w=deferred();waits.push(w);const child={kill:()=>{killed.push(id);w.resolve();}};(j.children ||= new Set()).add(child);j.child=child;
   await w.promise;j.children.delete(child);return rows(body.evaluations);
  }});
  const running=advanceCases(j,evaluator);assert.equal(waits.length,8);cancelJob(j);await running;
  assert.deepEqual(killed,Array.from({length:8},(_,i)=>i));assert.equal(j.index,0);assert.equal(j.results.length,0);assert.equal(cache.size,0);assert.equal(j.pendingGpuResults,undefined);
 }finally{os.cpus=original;}
});

test('a failed batch waits for siblings before surfacing failure',async()=>{
 const original=os.cpus;os.cpus=()=>Array(6).fill({});
 try{
  const j=job(64),w=deferred();let calls=0,done=false;
  const p=advanceCases(j,{isCached:()=>false,many:async items=>{if(calls++===0)throw Error('worker failed');await w.promise;return rows(items);}});
  p.catch(()=>{done=true;});await tick();assert.equal(done,false);w.resolve();await assert.rejects(p,/worker failed/);assert.equal(j.index,0);
 }finally{os.cpus=original;}
});

test('other job kinds and backends stay sequential',async()=>{
 for(const [kind,backend] of [['batch','native_detail'],['optimize','metal_detail'],['search','native_detail'],['optimize','cpu']]){
  const j=job(65,kind,backend);let active=0,peak=0;
  await advanceCases(j,{isCached:()=>false,many:async items=>{peak=Math.max(peak,++active);await tick();active--;return rows(items);}});
  assert.equal(peak,1);assert.equal(j.index,65);
 }
});

test('native host budgets travel only in internal service envelopes',async()=>{
 const calls=[],j=job(2);
 const evaluator=createEvaluator({keyOf:JSON.stringify,worker:async body=>{calls.push(body);return rows(body.evaluations);}});
 await advanceCases(j,evaluator);
 assert.equal(calls[0].host_threads,Math.min(2,os.cpus().length));assert.equal(calls[0].verification,'deferred');
 assert.ok(calls[0].evaluations.every(b=>!('host_threads' in b)));
});

test('process-group cancellation targets descendants and handles already-exited groups',()=>{
 const calls=[],child={pid:42,kill:()=>false};ownNativeProcessGroup(child,true,(...args)=>calls.push(args));
 assert.equal(child.kill(),true);assert.equal(child.kill('SIGKILL'),true);assert.deepEqual(calls,[[-42,'SIGTERM'],[-42,'SIGKILL']]);
 ownNativeProcessGroup(child,true,()=>{throw Object.assign(Error(),{code:'ESRCH'});});assert.equal(child.kill(),false);
 const ordinary={kill:()=>123};ownNativeProcessGroup(ordinary,false);assert.equal(ordinary.kill(),123);
});


test('concurrent candidates retain Unit 3 pause, displayed/sample checks and mismatch escalation',async()=>{
 const original=os.cpus;os.cpus=()=>Array(12).fill({});
 try{
  for(const mismatch of [false,true]){
   const j=job(128);Object.assign(j,{id:'unit4-integration',teamCount:1,groups:[],selectionBackend:'cpu'});
   for(const c of j.cases)c.evaluation.squad=Array.from({length:5},(_,i)=>`${c.evaluation.id}:${i}`);
   let candidateCalls=0;const checked=new Set();
   const result=(body,damage=body.id+1)=>({members:body.squad.map(name=>({name})),total_damage:damage,compute:{backend:'native_detail',capture_id:String(body.id),cpu_verification:{status:'pending'}}});
   const evaluator=createEvaluator({keyOf:JSON.stringify,worker:async request=>{
    await tick();
    if(request.action==='verify_portable_detail')return request.evaluations.map(({body})=>{
     checked.add(body.id);const matched=!(mismatch&&body.id===127),cpu=result(body,matched?body.id+1:0);
     if(!matched)cpu.compute={backend:'cpu',gpu_result_rejected:true};
     return {matched,differing_fields:matched?[]:['total_damage'],cpu_result:cpu};
    });
    candidateCalls++;j.pauseRequested=true;return request.evaluations.map(body=>({result:result(body)}));
   }});
   await run(j,{evaluator});assert.equal(candidateCalls,8);assert.equal(j.status,'paused');assert.equal(j.index,1);
   assert.ok(view(j).recommendation);j.pauseRequested=false;await run(j,{evaluator});
   assert.equal(j.status,'complete');assert.equal(j.index,128);assert.equal(candidateCalls,8);
   const recommendation=view(j).recommendation;assert.ok(recommendation);assert.ok(checked.has(Number(recommendation.teams[0].squad[0].split(':')[0])));
   assert.equal(j.verification.escalated,mismatch);
   if(mismatch){assert.equal(checked.size,128);assert.equal(recommendation.damage,127);}
   else {assert.equal(recommendation.damage,128);assert.ok(checked.size<128);}
  }
 }finally{os.cpus=original;}
});

test('native optimize defaults to 16 and retains only the 16/32 test override',async()=>{
 const original=os.cpus;os.cpus=()=>Array(2).fill({});
 try{
  for(const size of [undefined,16,32]){
   const sizes=[],threads=[],j=job(65);
   await advanceCases(j,{isCached:()=>false,many:async(items,j,options)=>{sizes.push(items.length);threads.push(options.hostThreads);return rows(items);}},{...(size===undefined?{}:{nativeBatchSize:size})});
   assert.deepEqual(sizes,size===32?[32,32,1]:[16,16,16,16,1]);
   assert.deepEqual(threads,sizes.map(n=>Math.min(n,2)));
  }
  for(const size of [0,8,17,33])await assert.rejects(advanceCases(job(1),{}, {nativeBatchSize:size}),/Invalid native candidate batch size/);
 }finally{os.cpus=original;}
});
