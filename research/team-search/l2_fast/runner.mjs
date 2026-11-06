// Standalone WASM runner: binary stdin u32[5] -> binary stdout f64[total,5 members].
// Benchmark mode owns a table/memory per worker; generation is outside kernel time.
import fs from 'node:fs';
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import {performance} from 'node:perf_hooks';
export function load(wasm,table){
  const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(wasm)),{env:{emscripten_notify_memory_growth(){}}}).exports;e._initialize();
  const raw=fs.readFileSync(table),n=Number(raw.readBigUInt64LE(8)),p=e.alloc(n*8);new Uint8Array(e.memory.buffer,p,n*8).set(raw.subarray(16,16+n*8));const t=e.l2_create(p,n);e.release(p);if(!t)throw Error('table load');return {e,t};
}
const args=process.argv.slice(2),opt=k=>args[args.indexOf(k)+1];
if(isMainThread&&args.includes('--bench')){
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
