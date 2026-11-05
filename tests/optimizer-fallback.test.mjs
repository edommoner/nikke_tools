import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import {createEvaluator,advanceCases} from '../app/evaluation-queue.mjs';
import {cancelJob} from '../server.mjs';
const tick=()=>new Promise(r=>setImmediate(r));
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const body=id=>({id,compute_backend:'native_detail'});
const job=n=>({kind:'optimize',status:'running',index:0,results:[],cases:Array.from({length:n},(_,id)=>({value:id,evaluation:body(id)}))});
const pending=id=>({result:{cpu_fallback_pending:{capture_id:String(id)}}});
const cpu=id=>({total_damage:id,compute:{backend:'cpu',capture_id:String(id)}});

test('fallbacks start before later native waves and complete out of order with ordered publication/cache',async()=>{
 const original=os.cpus;os.cpus=()=>Array(3).fill({});
 try{
  const j=job(65),cache=new Map(),waits=new Map(),native=[];
  const e=createEvaluator({cache,keyOf:JSON.stringify,worker:async request=>{
   if(request.action==='cpu_fallback_portable_detail'){
    const id=request.evaluations[0].body.id,w=deferred();waits.set(id,w);await w.promise;return [cpu(id)];
   }
   native.push(request.evaluations[0].id);
   return request.evaluations.map(b=>b.id===0||b.id===33?pending(b.id):{result:cpu(b.id)});
  }});
  const p=advanceCases(j,e);await tick();
  assert.deepEqual(native,[0,16,32,48,64]);assert.equal(waits.size,2);assert.equal(j.index,0);
  assert.equal(cache.has(JSON.stringify(body(0))),false);
  waits.get(33).resolve();await tick();assert.equal(j.index,0);
  waits.get(0).resolve();await p;
  assert.deepEqual(j.results.map(r=>r.value),Array.from({length:65},(_,i)=>i));
  assert.equal(j.index,65);assert.equal(cache.size,65);assert.equal(e.isCached(body(0)),true);
 }finally{os.cpus=original;}
});

test('fallback and verification children share the process bound across evaluators',async()=>{
 const original=os.cpus;os.cpus=()=>Array(3).fill({});
 try{
  let active=0,peak=0;const waits=[];
  const worker=async request=>{
   if(request.action==='evaluate_portable_detail_batch')return request.evaluations.map(b=>pending(b.id));
   active++;peak=Math.max(peak,active);const w=deferred();waits.push(w);await w.promise;active--;
   return request.action==='verify_portable_detail'?[{matched:true,differing_fields:[],cpu_result:cpu(9)}]:[cpu(request.evaluations[0].body.id)];
  };
  const e=createEvaluator({keyOf:JSON.stringify,worker}),other=createEvaluator({keyOf:JSON.stringify,worker});
  const j=job(3),p=e.many(j.cases.map(c=>c.evaluation),j);
  const v=other.verify([{body:body(9),result:{compute:{capture_id:'9'}}}],job(1));
  await tick();assert.equal(waits.length,2);
  for(let i=0;i<4;i++){waits[i].resolve();await tick();}
  await Promise.all([p,v]);assert.equal(peak,2);
 }finally{os.cpus=original;}
});

test('pause drains fallbacks, resumes and extends without replay',async()=>{
 const j=job(3),w=deferred();let calls=0;
 const e=createEvaluator({keyOf:JSON.stringify,worker:async request=>{
  if(request.action==='cpu_fallback_portable_detail'){await w.promise;return [cpu(1)];}
  calls++;return request.evaluations.map(b=>b.id===1?pending(1):{result:cpu(b.id)});
 }});
 const p=advanceCases(j,e);await tick();j.pauseRequested=true;await tick();assert.equal(j.status,'running');
 w.resolve();await p;assert.equal(j.status,'paused');assert.equal(j.pendingGpuResults.rows.length,1);
 j.pauseRequested=false;j.status='running';await advanceCases(j,e);assert.equal(j.index,3);assert.equal(calls,1);
 j.cases.push({value:3,evaluation:body(3)});await advanceCases(j,e);assert.equal(j.index,4);assert.equal(calls,2);
});

test('cancel kills fallback children, drops queued work and prevents late cache/publication',async()=>{
 const original=os.cpus;os.cpus=()=>Array(2).fill({});
 try{
  const j=job(3),cache=new Map();let started=0,killed=0;
  const e=createEvaluator({cache,keyOf:JSON.stringify,worker:async request=>{
   if(request.action==='evaluate_portable_detail_batch')return request.evaluations.map(b=>pending(b.id));
   started++;const w=deferred(),child={kill:()=>{killed++;w.resolve();}};(j.children ||= new Set()).add(child);
   await w.promise;j.children.delete(child);return [cpu(0)];
  }});
  const p=advanceCases(j,e);await tick();cancelJob(j);await p;
  assert.equal(started,1);assert.equal(killed,1);assert.equal(cache.size,0);assert.equal(j.index,0);assert.deepEqual(j.results,[]);
 }finally{os.cpus=original;}
});

test('unscoped marker fails without CPU launch or caching',async()=>{
 for(const kind of ['batch','single']){
  const cache=new Map();let calls=0;
  const e=createEvaluator({cache,keyOf:JSON.stringify,worker:async()=>{calls++;return [pending(0)];}});
  const rows=await e.many([body(0)],{kind,status:'running'});
  assert.match(rows[0].error,/Unexpected/);assert.equal(calls,1);assert.equal(cache.size,0);
 }
});

test('contiguous completed prefix publishes while following native batches are still running',async()=>{
 const original=os.cpus;os.cpus=()=>Array(1).fill({});
 try{
  const j=job(65),fallback=deferred(),native=deferred();let calls=0;
  const e=createEvaluator({keyOf:JSON.stringify,worker:async request=>{
   if(request.action==='cpu_fallback_portable_detail'){await fallback.promise;return [cpu(1)];}
   if(++calls===2)await native.promise;
   return request.evaluations.map(b=>b.id===1?pending(1):{result:cpu(b.id)});
  }});
  const p=advanceCases(j,e);await tick();assert.equal(calls,2);assert.equal(j.index,1);
  fallback.resolve();await tick();assert.equal(j.index,16);
  j.pauseRequested=true;native.resolve();await p;
  assert.equal(calls,2);assert.equal(j.index,17);assert.equal(j.pendingGpuResults.rows.length,15);
  j.status='running';j.pauseRequested=false;await advanceCases(j,e);assert.equal(j.index,65);assert.equal(calls,5);
 }finally{os.cpus=original;}
});
