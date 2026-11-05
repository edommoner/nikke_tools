import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {attachBrowser,cancelBrowser,acceptBrowserResults,browserWasm} from '../app/browser-transport.mjs';
import {createEvaluator,advanceCases} from '../app/evaluation-queue.mjs';
const wire={input_sha256:'a'.repeat(64),wasm_identity:'b'.repeat(64)};
const upload={input_sha256:wire.input_sha256,readback_gzip_base64:'AAAA',browser_seconds:.2};
function setup(n=3){
 const job={status:'running',index:0,results:[],kind:'batch',cases:Array.from({length:n},(_,id)=>({value:id,evaluation:{id,compute_backend:'browser_detail'}}))};attachBrowser(job);
 const calls=[];const evaluator=createEvaluator({keyOf:JSON.stringify,worker:async req=>{calls.push(req);return req.action==='prepare_browser_wires'?req.evaluations.map(b=>b.id===1?{result:{total_damage:11}}:{wire}):req.evaluations.map(b=>({result:{total_damage:b.id,compute:{backend:'browser_detail'}}}));}});
 return {job,calls,evaluator};
}
async function awaiting(job){for(let i=0;i<50&&!job.awaitingBrowser;i++)await new Promise(r=>setImmediate(r));assert.ok(job.awaitingBrowser);return job.awaitingBrowser;}
function submit(job,request){acceptBrowserResults(job,{token:request.token,results:request.rows.map(()=>upload),worker_count:2},'Test UA');}
test('awaiting browser exposes sparse row indices, finishes only wires and keeps passthrough in order',async()=>{
 const {job,calls,evaluator}=setup();const running=advanceCases(job,evaluator),request=await awaiting(job);
 assert.deepEqual(request.rows.map(r=>r.index),[0,2]);assert.equal(job.index,0);assert.equal(calls.length,1);
 submit(job,request);await running;
 assert.equal(job.awaitingBrowser,undefined);assert.deepEqual(calls[1].evaluations.map(b=>b.id),[0,2]);
 assert.match(calls[1].uploads[0].device,/Test UA.*workers=2/);assert.deepEqual(job.results.map(r=>r.result.total_damage),[0,11,2]);
 assert.throws(()=>submit(job,request),/一致/);
});
test('cancel while awaiting rejects wait and publishes no results',async()=>{
 const {job,calls,evaluator}=setup();const running=advanceCases(job,evaluator);await awaiting(job);
 job.status='cancelled';cancelBrowser(job);await running;
 assert.equal(job.index,0);assert.deepEqual(job.results,[]);assert.equal(calls.length,1);assert.equal(job.awaitingBrowser,undefined);
});
test('pause waits for actual result then resumes saved remaining rows',async()=>{
 const {job,calls,evaluator}=setup();const running=advanceCases(job,evaluator),request=await awaiting(job);
 job.pauseRequested=true;assert.equal(job.status,'running');submit(job,request);await running;
 assert.equal(job.status,'paused');assert.equal(job.index,1);assert.equal(job.pendingGpuResults.rows.length,2);
 job.pauseRequested=false;job.status='running';await advanceCases(job,evaluator);assert.equal(calls.length,2);assert.equal(job.index,3);
});
test('invalid result shapes/tokens/hashes/times/worker counts do not consume request',async()=>{
 const job={status:'running'};attachBrowser(job);const wait=job.browser.request([{index:0,wire}]),request=job.awaitingBrowser;
 const valid={token:request.token,results:[upload],worker_count:1};
 for(const changed of [{token:'stale'},{results:[]},{results:[null]},{results:[{...upload,input_sha256:'c'.repeat(64)}]},{results:[{...upload,readback_gzip_base64:'!'}]},{results:[{...upload,browser_seconds:NaN}]},{results:[{...upload,browser_seconds:-1}]},{worker_count:33},{worker_count:true}]){
   assert.throws(()=>acceptBrowserResults(job,{...valid,...changed}));assert.equal(job.awaitingBrowser,request);
 }
 acceptBrowserResults(job,valid);assert.equal((await wait).length,1);
});
test('browser needs a job even if a result was cached',async()=>{
 const evaluator=createEvaluator({keyOf:JSON.stringify,worker:async()=>{throw Error('must not run');}});
 await assert.rejects(evaluator.one({compute_backend:'browser_detail'}),/ジョブ/);
});
test('32 browser rows prepare in one worker batch',async()=>{
 const {job,calls,evaluator}=setup(32),running=advanceCases(job,evaluator),request=await awaiting(job);submit(job,request);await running;
 assert.equal(calls[0].evaluations.length,32);assert.equal(job.index,32);
});
test('wasm route helper admits only built identity, verifies receipt and binary hashes',()=>{
 const root=mkdtempSync(path.join(os.tmpdir(),'wasm-route-'));try{
   const hash=b=>createHash('sha256').update(b).digest('hex');
   const data={compiler_version:'fixture',flags:['-O2'],sources:{'host.cpp':'a','kernel.cpp':'b'}};
   const identity=hash(JSON.stringify(data)),dir=path.join(root,'research/portable-build/wasm',identity),raw=Buffer.from('wasm fixture');mkdirSync(dir,{recursive:true});
   writeFileSync(path.join(dir,'product.wasm'),raw);writeFileSync(path.join(dir,'build.json'),JSON.stringify({...data,identity,wasm_sha256:hash(raw)}));
   assert.deepEqual(browserWasm(root,identity),raw);
   for(const id of ['../bad','A'.repeat(64),'c'.repeat(64)])assert.throws(()=>browserWasm(root,id));
   writeFileSync(path.join(dir,'product.wasm'),'corrupt');assert.throws(()=>browserWasm(root,identity),/identity/);
 }finally{rmSync(root,{recursive:true,force:true});}
});

test('actual routes serve worker with restrictive wasm CSP and reject unknown identities/jobs',async()=>{
 const {Readable}=await import('node:stream');const {server}=await import('../server.mjs');
 const request=(url,method='GET',data)=>new Promise(resolve=>{
   const req=Readable.from(data?[JSON.stringify(data)]:[]);Object.assign(req,{url,method,headers:{host:'127.0.0.1:4317'}});
   const res={writeHead(status,headers){this.status=status;this.headers=headers;},end(raw){resolve({status:this.status,headers:this.headers,raw});}};
   server.emit('request',req,res);
 });
 const worker=await request('/browser-worker.js');assert.equal(worker.status,200);assert.match(worker.headers['Content-Security-Policy'],/script-src 'self' 'wasm-unsafe-eval'; worker-src 'self';/);
 assert.match(String(worker.raw),/CompressionStream/);
 const wasm=await request('/api/browser-wasm/'+'a'.repeat(64));assert.equal(wasm.status,404);
 const job=await request('/api/jobs/missing/browser-results','POST',{token:'stale',results:[]});assert.equal(job.status,404);
});
test('UI includes browser backend, verified request flag, reported time and worker polling',async()=>{
 const {readFileSync}=await import('node:fs');const {runInNewContext}=await import('node:vm');
 const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8');
 const line=source.split('\n').find(line=>line.startsWith('function computeDetailsCore('));
 const rendered=runInNewContext(source.split('\n').find(line=>line.startsWith('function verificationLabel('))+'\n'+line+'\ncomputeDetailsCore(result)',{result:{compute:{backend:'browser_detail',device:'UA workers=2',browser_seconds:.1,elapsed_ms:120,cpu_verification:{matched:true}}},e:v=>v});
 assert.match(rendered,/ブラウザ計算 · UA workers=2/);assert.match(rendered,/0.100秒（ブラウザ申告）/);
 assert.match(source,/verify_detail:\[[^\]]*'browser_detail'/);assert.match(source,/hardware.browser\?\.available/);
 assert.match(source,/ブラウザで計算中/);assert.match(source,/new Worker\('\/browser-worker.js'\)/);
});

test('documented results shape works without optional worker-count metadata',async()=>{
 const job={status:'running'};attachBrowser(job);const wait=job.browser.request([{index:0,wire}]);
 acceptBrowserResults(job,{token:job.awaitingBrowser.token,results:[upload]},'UA');
 assert.match((await wait)[0].device,/UA.*workers=unreported/);
});
