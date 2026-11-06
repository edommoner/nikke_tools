// Product WASM runner. Prepare with bench_wasm_prepare.py; each worker owns its
// instances/memory. Readbacks are compared in memory and never written to disk.
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {spawnSync} from 'node:child_process';
const sha=b=>createHash('sha256').update(b).digest('hex');
if(isMainThread){
  const args=process.argv.slice(2), opt=k=>args[args.indexOf(k)+1];
  if(!args.includes('--manifest'))throw Error('usage: --manifest FILE --workers N --variant soft|hard|compare [--evidence JSONL]');
  const manifest=JSON.parse(fs.readFileSync(opt('--manifest'),'utf8'));
  const workers=Number(opt('--workers')),variant=opt('--variant');
  if(!Number.isInteger(workers)||workers<1||!['soft','hard','compare'].includes(variant))throw Error('invalid options');
  const rows=manifest.rows.filter(r=>r.status==='prepared');
  if(!rows.length)throw Error('empty manifest');
  const evidence=args.includes('--evidence')?fs.openSync(opt('--evidence'),'a'):null;
  let next=0,done=0,kernelMs=0,failed=0;
  const pool=[],started=performance.now();
  try{
    await new Promise((resolve,reject)=>{
      for(let i=0;i<workers;i++){
        const w=new Worker(new URL(import.meta.url),{workerData:{variant}});pool.push(w);
        let stopping=false;
        const feed=()=>{if(next<rows.length)w.postMessage(rows[next++]);else{stopping=true;w.postMessage(null);}};
        w.on('error',reject);
        w.on('exit',code=>{if(code!==0||!stopping)reject(Error('worker exited '+code));});
        w.on('message',m=>{
          done++;kernelMs+=m.kernel_ms;
          if(m.status!=='identical'&&m.status!=='completed')failed++;
          if(evidence!==null){const {kernel_ms,...record}=m;fs.writeSync(evidence,JSON.stringify(record)+'\n');}
          if(done===rows.length)resolve();else feed();
        });feed();
      }
    });
  }finally{
    await Promise.all(pool.map(w=>w.terminate()));
    if(evidence!==null)fs.closeSync(evidence);
  }
  const seconds=(performance.now()-started)/1000;
  console.log(JSON.stringify({engine:'node '+process.version,workers,variant,cases:done,failed,
    seconds,ms_per_squad:seconds*1000/done,kernel_ms_sum:kernelMs,
    timing_scope:'worker startup, WASM initialization, input reads/inflate/hashes, alloc/run/readback hash/release, messages and termination; excludes Python preparation'}));
  if(done!==rows.length||failed)process.exitCode=1;
}else{
  const instances=new Map();
  function run(file,input,bytes){
    let e=instances.get(file);
    if(!e){e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file)),{env:{emscripten_notify_memory_growth(){}}}).exports;e._initialize();instances.set(file,e);}
    const ip=e.alloc(input.length),op=e.alloc(bytes);
    if(!ip||!op)throw Error('WASM allocation failed');
    try{
      new Uint8Array(e.memory.buffer,ip,input.length).set(input);
      const start=performance.now(),rc=e.run(ip,input.length/4,op,bytes/4),ms=performance.now()-start;
      // A copy is necessary only during comparisons, before the next allocation.
      const view=Buffer.from(e.memory.buffer,op,bytes);
      return {rc,ms,sha256:sha(view),...(workerData.variant==='compare'?{raw:Buffer.from(view)}:{})};
    }finally{e.release(ip);e.release(op);}
  }
  parentPort.on('message',row=>{
    if(row===null){parentPort.close();return;}
    const stored=fs.readFileSync(row.input),input=stored[0]===31&&stored[1]===139?gunzipSync(stored):stored,bytes=row.output_words*4;
    if(input.length!==(row.input_words+1)*4||sha(input)!==row.input_sha256)throw Error('input changed '+row.id);
    if(workerData.variant!=='compare'){
      const r=run(row[workerData.variant],input,bytes);
      const same=r.rc===0&&(!row.expected_sha256||r.sha256===row.expected_sha256);
      parentPort.postMessage({id:row.id,status:same?'completed':'failed',rc:r.rc,sha256:r.sha256,kernel_ms:r.ms});return;
    }
    const a=run(row.soft,input,bytes),b=run(row.hard,input,bytes);
    const same=a.rc===0&&b.rc===0&&a.raw.equals(b.raw);
    const result={id:row.id,length:bytes,input_sha256:row.input_sha256,status:same?'identical':'different',
      soft:{rc:a.rc,sha256:a.sha256},hard:{rc:b.rc,sha256:b.sha256},kernel_ms:a.ms+b.ms};
    if(row.native){
      // A FIFO in the owned input directory carries native bytes in memory.
      // stdout carries the host receipt. No regular readback file is created.
      const pipe=`import gzip,os,pathlib,select,subprocess,sys,tempfile,time
with tempfile.TemporaryDirectory(prefix='native-pipe-',dir=pathlib.Path(sys.argv[2]).parent) as tmp:
 stored=pathlib.Path(sys.argv[2]);inp=stored
 if stored.read_bytes()[:2]==bytes([31,139]):
  inp=pathlib.Path(tmp)/'input.bin';inp.write_bytes(gzip.decompress(stored.read_bytes()))
 fifo=pathlib.Path(tmp)/'output';os.mkfifo(fifo)
 fd=os.open(fifo,os.O_RDWR|os.O_NONBLOCK)
 try:
  p=subprocess.Popen([sys.argv[1],str(inp),str(fifo),*sys.argv[3:]],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  raw=bytearray();deadline=time.monotonic()+240
  while True:
   try:
    chunk=os.read(fd,1048576)
    if chunk:raw.extend(chunk);continue
   except BlockingIOError:pass
   if p.poll() is not None:break
   if time.monotonic()>deadline:p.kill();raise TimeoutError('native pipe')
   select.select([fd],[],[],0.01)
  out,err=p.communicate();sys.stdout.buffer.write(raw);sys.stdout.buffer.write(out);sys.stderr.buffer.write(err);sys.exit(p.returncode)
 finally:os.close(fd)
`;
      const n=spawnSync(row.native_python??'python3.12',['-c',pipe,row.native,row.input,String(row.input_words),String(row.output_words),'1'],{maxBuffer:bytes+1024*1024,timeout:300000});
      if(n.error)throw n.error;
      if(n.status!==0||n.stdout.length<=bytes)throw Error(JSON.stringify({id:row.id,native_rc:n.status,stdout_length:n.stdout.length,expected_bytes:bytes,stderr:n.stderr.toString()}));
      const raw=n.stdout.subarray(0,bytes),receipt=JSON.parse(n.stdout.subarray(bytes).toString());
      const nativeSame=n.status===0&&receipt.command_status==='completed'&&receipt.output_bytes===bytes&&receipt.cases===1&&raw.length===bytes&&b.raw.equals(raw);
      result.native={rc:n.status,length:raw.length,sha256:sha(raw),status:nativeSame?'identical':'different'};
      if(!nativeSame)result.status='different';
    }
    parentPort.postMessage(result);
  });
}
