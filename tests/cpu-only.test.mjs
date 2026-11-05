import test from 'node:test';
import assert from 'node:assert/strict';
import {Readable} from 'node:stream';
import {createEvaluator} from '../app/evaluation-queue.mjs';
import {server} from '../server.mjs';

test('removed device detail backends are rejected before workers run',async()=>{
 const evaluator=createEvaluator({worker:()=>{throw Error('worker must not run');},keyOf:JSON.stringify});
 for(const compute_backend of ['cuda_detail','cuda_verified','cuda_shared_detail','metal_detail']){
  const [row]=await evaluator.many([{compute_backend}]);assert.match(row.error,/未対応/);
 }
});
test('hardware endpoint exposes only native and browser availability',async()=>{
 const result=await new Promise(resolve=>{
  const req=Readable.from([]);Object.assign(req,{url:'/api/hardware',method:'GET',headers:{host:'127.0.0.1:4317'}});
  const res={writeHead(status){this.status=status;},end(raw){resolve({status:this.status,value:JSON.parse(raw)});}};
  server.emit('request',req,res);
 });
 assert.equal(result.status,200);assert.deepEqual(Object.keys(result.value).sort(),['browser','native']);
 assert.equal(typeof result.value.native.available,'boolean');assert.equal(typeof result.value.browser.available,'boolean');
});
