import test from 'node:test';
import assert from 'node:assert/strict';
import {createEvaluator,advanceCases} from '../app/evaluation-queue.mjs';
const body=id=>({id,compute_backend:'cuda_detail'});
const make=worker=>createEvaluator({worker,keyOf:JSON.stringify});
const job=(kind='search',count=3)=>({kind,status:'running',index:0,results:[],target:2,cases:Array.from({length:count},(_,i)=>({value:i,evaluation:body(i)}))});
test('mixed cache, duplicates, CPU, invalid and GPU failures preserve input order',async()=>{
 const calls=[];
 const evaluator=make(async request=>{
   calls.push(request);
   if(request.action==='evaluate')return {total_damage:request.id};
   return request.evaluations.map(b=>b.id===3?{error:'unsupported input'}:{result:{total_damage:b.id,compute:{backend:'cuda_detail'}}});
 });
 await evaluator.one(body(0));calls.length=0;
 const rows=await evaluator.many([body(2),body(0),body(2),{id:9},body(3),{compute_backend:'invalid'}]);
 assert.deepEqual(rows.slice(0,4).map(r=>r.result.total_damage),[2,0,2,9]);
 assert.equal(rows[1].result.cache_hit,true);assert.equal(rows[0].result.cache_hit,false);
 assert.deepEqual(calls[0].evaluations.map(b=>b.id),[2,3]);assert.equal(calls.length,2);
 assert.equal(rows[4].error,'unsupported input');assert.ok(rows[5].error);
 rows[0].result.total_damage=999;assert.equal((await evaluator.one(body(2))).total_damage,2);
});
test('GPU unavailability falls back with honest labels; malformed output is not cached',async()=>{
 const evaluator=make(async r=>{if(r.action==='evaluate_detail_batch')throw Object.assign(Error('offline'),{gpuUnavailable:true});return {total_damage:r.id};});
 const rows=await evaluator.many([body(1),body(2)]);
 assert.ok(rows.every(r=>r.result.compute.backend==='cpu'&&r.result.compute.requested==='cuda_detail'));
 const malformed=make(async()=>[]);
 assert.ok((await malformed.many([body(1)]))[0].error);assert.equal(malformed.isCached(body(1)),false);
});
test('pause commits one ordered result and resume reuses the remaining computed batch',async()=>{
 let calls=0;const j=job();
 const evaluator=make(async r=>{calls++;j.pauseRequested=true;return r.evaluations.map(b=>({result:{total_damage:b.id}}));});
 await advanceCases(j,evaluator);assert.equal(j.status,'paused');assert.equal(j.index,1);
 j.pauseRequested=false;j.status='running';await advanceCases(j,evaluator);
 assert.equal(calls,1);assert.deepEqual(j.results.map(r=>r.value),[0,1,2]);
 assert.deepEqual(j.results.map(r=>r.meets),[false,false,true]);
});
test('cancel publishes nothing; search fails in order; optimize advances over errors; cap is 32',async()=>{
 const cancelled=job();
 await advanceCases(cancelled,make(async r=>{cancelled.status='cancelled';return r.evaluations.map(()=>({result:{total_damage:1}}));}));
 assert.equal(cancelled.index,0);assert.deepEqual(cancelled.results,[]);
 const evaluator=make(async r=>r.evaluations.map(b=>b.id===1?{error:'bad'}:{result:{total_damage:b.id}}));
 const search=job();await assert.rejects(advanceCases(search,evaluator),/bad/);assert.equal(search.index,1);
 const optimize=job('optimize',34);await advanceCases(optimize,evaluator);
 assert.equal(optimize.index,34);assert.equal(optimize.results[1].error,'bad');
 await assert.rejects(evaluator.many(Array.from({length:33},(_,i)=>body(i))),/32/);
});
test('shared Metal uses isolated product workers and the same ordered cache',async()=>{
 const calls=[];
 const evaluator=make(async request=>{
   calls.push(request);
   if(request.action==='evaluate')return {total_damage:request.id};
   return request.evaluations.map(b=>({result:{total_damage:b.id,compute:{backend:b.compute_backend}}}));
 });
 const metal=id=>({id,compute_backend:'metal_detail'});
 const rows=await evaluator.many([metal(1),body(2),metal(3),metal(1),{id:4}]);
 assert.deepEqual(rows.map(r=>r.result.total_damage),[1,2,3,1,4]);
 assert.deepEqual(calls.map(r=>r.action),['evaluate_detail_batch','evaluate_portable_detail_batch','evaluate_portable_detail_batch','evaluate']);
 assert.ok(calls.filter(r=>r.action==='evaluate_portable_detail_batch').every(r=>r.evaluations.length===1));
 assert.equal((await evaluator.one(metal(1))).cache_hit,true);assert.equal(calls.length,4);
});
test('shared Metal worker unavailability falls back with its own requested label',async()=>{
 const evaluator=make(async request=>{
   if(request.action==='evaluate_portable_detail_batch')throw Object.assign(Error('offline'),{gpuUnavailable:true});
   return {total_damage:7};
 });
 const result=await evaluator.one({id:7,compute_backend:'metal_detail'});
 assert.equal(result.compute.backend,'cpu');assert.equal(result.compute.requested,'metal_detail');
});
test('shared CUDA uses the common isolated service and stays distinct from legacy CUDA',async()=>{
 const calls=[];
 const evaluator=make(async request=>{calls.push(request);return request.evaluations.map(b=>({result:{total_damage:b.id,compute:{backend:b.compute_backend}}}));});
 const shared={id:1,compute_backend:'cuda_shared_detail'},metal={id:2,compute_backend:'metal_detail'};
 const rows=await evaluator.many([shared,body(3),metal,shared]);
 assert.deepEqual(rows.map(r=>r.result.total_damage),[1,3,2,1]);
 assert.deepEqual(calls.map(r=>r.action),['evaluate_detail_batch','evaluate_portable_detail_batch','evaluate_portable_detail_batch']);
 assert.ok(calls.filter(r=>r.action==='evaluate_portable_detail_batch').every(r=>r.evaluations.length===1));
 assert.equal((await evaluator.one(shared)).cache_hit,true);assert.equal(calls.length,3);
});

test('explicit noncached execution never replays results or stale CPU fallbacks',async()=>{
 const cache=new Map();let calls=0;
 const evaluator=createEvaluator({cache,keyOf:JSON.stringify,cacheable:b=>b.compute_backend!=='cuda_shared_detail',worker:async request=>{
  calls++;return request.action==='evaluate_portable_detail_batch'?[{result:{compute:{backend:calls===1?'cpu':'cuda_shared_detail'},value:calls}}]:{value:calls};
 }});
 const request={compute_backend:'cuda_shared_detail'};
 const first=await evaluator.one(request),second=await evaluator.one(request);
 assert.equal(first.compute.backend,'cpu');assert.equal(second.compute.backend,'cuda_shared_detail');
 assert.equal(calls,2);assert.equal(cache.size,0);assert.equal(first.cache_hit,false);assert.equal(second.cache_hit,false);
 const cpu={compute_backend:'cpu'};await evaluator.one(cpu);const cached=await evaluator.one(cpu);
 assert.equal(calls,3);assert.equal(cached.cache_hit,true);
});
