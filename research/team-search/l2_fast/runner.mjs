// Standalone WASM runner: binary stdin u32[5] -> binary stdout f64[total,5 members].
// Benchmark mode owns a table/memory per worker; generation is outside kernel time.
import fs from 'node:fs';
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import {performance} from 'node:perf_hooks';
export function load(wasm,table){
  let e; e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(wasm)),{env:{emscripten_notify_memory_growth(){}},wasi_snapshot_preview1:{clock_time_get(clock,precision,p){if(clock!==0&&clock!==1)return 28;new DataView(e.memory.buffer).setBigUint64(p,BigInt(Math.floor((clock===0?Date.now():performance.now())*1e6)),true);return 0;}}}).exports;e._initialize();
  const raw=fs.readFileSync(table),n=Number(raw.readBigUInt64LE(8)),p=e.alloc(n*8);new Uint8Array(e.memory.buffer,p,n*8).set(raw.subarray(16,16+n*8));const t=e.l2_create(p,n);e.release(p);if(!t)throw Error('table load');return {e,t};
}
const args=process.argv.slice(2),opt=k=>args[args.indexOf(k)+1];
export function enumeratePartition(wasm,table,roster,k,partition,partitions,stride=1){
  const {e,t}=load(wasm,table),ip=e.alloc(roster.length*4),op=e.alloc(k*32),np=e.alloc(4),cp=e.alloc(32);
  new Uint32Array(e.memory.buffer,ip,roster.length).set(roster);
  if(e.l2_enumerate_balanced(t,ip,roster.length,k,partition,partitions,stride,op,np,cp))throw Error('enumerate');
  const count=new DataView(e.memory.buffer).getUint32(np,true),entries=[];
  for(let i=0;i<count;i++){const v=new DataView(e.memory.buffer,op+i*32,32);entries.push({indices:Array.from({length:5},(_,j)=>v.getUint32(j*4,true)),score:v.getFloat64(24,true)});}
  const v=new DataView(e.memory.buffer,cp,32),counts={visited:Number(v.getBigUint64(0,true)),covered:Number(v.getBigUint64(8,true)),scored:Number(v.getBigUint64(16,true)),seconds:v.getFloat64(24,true)};
  for(const p of [ip,op,np,cp])e.release(p);e.l2_destroy(t);return {entries,counts};
}
const compare=(a,b)=>{if(a.score!==b.score)return b.score-a.score;for(let j=0;j<5;j++)if(a.indices[j]!==b.indices[j])return a.indices[j]-b.indices[j];return 0;};
if(!isMainThread&&workerData.enumerate){
  parentPort.postMessage(enumeratePartition(workerData.wasm,workerData.table,workerData.roster,workerData.k,workerData.partition,workerData.workers,workerData.stride));
}else if(isMainThread&&args.includes('--enumerate')){
  const workers=Number(opt('--workers')),k=args.includes('--k')?Number(opt('--k')):10000,roster=JSON.parse(fs.readFileSync(opt('--roster'),'utf8')),stride=args.includes('--stride')?Number(opt('--stride')):1,start=performance.now();
  if(!Number.isInteger(workers)||workers<1||workers>256||!Number.isInteger(k)||k<1||!Number.isInteger(stride)||stride<1)throw Error('invalid enumeration options');
  const results=await Promise.all(Array.from({length:workers},(_,partition)=>new Promise((resolve,reject)=>{
    const w=new Worker(new URL(import.meta.url),{workerData:{enumerate:true,wasm:opt('--wasm'),table:opt('--table'),roster,k,partition,workers,stride}});
    w.on('message',resolve);w.on('error',reject);w.on('exit',code=>{if(code)reject(Error('worker exit '+code));});
  })));
  const counts={visited:0,covered:0,scored:0,seconds:(performance.now()-start)/1000};for(const r of results)for(const key of ['visited','covered','scored'])counts[key]+=r.counts[key];
  console.log(JSON.stringify({entries:results.flatMap(r=>r.entries).sort(compare).slice(0,k),counts,partition_seconds:results.map(r=>r.counts.seconds)}));
}else if(isMainThread&&args.includes('--bench')){
  const workers=Number(opt('--workers')),count=Number(opt('--count')),started=performance.now();
  const barrier=new SharedArrayBuffer(8);
  const results=await Promise.all(Array.from({length:workers},(_,i)=>new Promise((resolve,reject)=>{
    const w=new Worker(new URL(import.meta.url),{workerData:{wasm:opt('--wasm'),table:opt('--table'),input:args.includes('--input')?opt('--input'):null,count:Math.floor(count/workers)+(i<count%workers?1:0),first:i*Math.floor(count/workers)+Math.min(i,count%workers),workers,barrier,seed:190019+i}});
    w.on('message',resolve);w.on('error',reject);w.on('exit',code=>{if(code)reject(Error('worker exit '+code));});
  })));
  console.log(JSON.stringify({workers,count,wall_seconds:(performance.now()-started)/1000,kernel_seconds:results.map(r=>r.seconds),kernel_ns_per_squad:results[0].batch_seconds.reduce((sum,_,i)=>sum+Math.max(...results.map(r=>r.batch_seconds[i])),0)*1e9/count,results,scope:'sum of per-batch maximum worker kernel seconds / total count; synchronized starts; wall includes startup, table load, generation, barriers and readback'}));
}else if(!isMainThread){
  const {e,t}=load(workerData.wasm,workerData.table),batch=8192,ip=e.alloc(batch*20),op=e.alloc(batch*8);let seed=workerData.seed,seconds=0,checksum=0;const batch_seconds=[],sync=new Int32Array(workerData.barrier);
  function barrier(){const generation=Atomics.load(sync,1);if(Atomics.add(sync,0,1)===workerData.workers-1){Atomics.store(sync,0,0);Atomics.add(sync,1,1);Atomics.notify(sync,1);}else while(Atomics.load(sync,1)===generation)Atomics.wait(sync,1,generation);}
  const input=workerData.input?fs.readFileSync(workerData.input):null;
  for(let offset=0;offset<workerData.count;offset+=batch){const n=Math.min(batch,workerData.count-offset);
    if(input){const dst=new Uint32Array(e.memory.buffer,ip,n*5),src=new Uint32Array(input.buffer,input.byteOffset,input.length/4);for(let i=0;i<n;i++)dst.set(src.subarray(((workerData.first+offset+i)%(src.length/5))*5,((workerData.first+offset+i)%(src.length/5))*5+5),i*5);}
    else seed=e.l2_generate(t,seed,ip,n,1);
    barrier();
    const start=performance.now();if(e.l2_score_many(t,ip,n,op,0))throw Error('score');const elapsed=(performance.now()-start)/1000;seconds+=elapsed;batch_seconds.push(elapsed);
    barrier();
    const view=new Float64Array(e.memory.buffer,op,n);for(const x of view)checksum+=x;
  }e.release(ip);e.release(op);e.l2_destroy(t);parentPort.postMessage({seconds,checksum,seed,batch_seconds});
}else{
  const {e,t}=load(opt('--wasm'),opt('--table'));const ip=e.alloc(4096*20),op=e.alloc(4096*8),mp=e.alloc(4096*40);let pending=Buffer.alloc(0);
  for await(const chunk of process.stdin){pending=Buffer.concat([pending,chunk]);let offset=0;
    while(pending.length-offset>=20){const n=Math.min(4096,Math.floor((pending.length-offset)/20));new Uint8Array(e.memory.buffer,ip,n*20).set(pending.subarray(offset,offset+n*20));if(e.l2_score_many(t,ip,n,op,mp))throw Error('invalid squad');const totals=new Float64Array(e.memory.buffer,op,n),members=new Float64Array(e.memory.buffer,mp,n*5),out=Buffer.alloc(n*48);for(let i=0;i<n;i++){out.writeDoubleLE(totals[i],i*48);for(let j=0;j<5;j++)out.writeDoubleLE(members[i*5+j],i*48+8+j*8);}if(!process.stdout.write(out))await new Promise(r=>process.stdout.once('drain',r));offset+=n*20;}
    pending=Buffer.from(pending.subarray(offset));
  }if(pending.length)throw Error('incomplete squad');e.release(ip);e.release(op);e.release(mp);e.l2_destroy(t);
}
