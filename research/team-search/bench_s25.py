"""S25 exact enumeration reuse experiments, sequential idle-gated timings."""
import argparse, ctypes as C, hashlib, json, os, subprocess, threading, time
from pathlib import Path
import bench_s23 as b
import bench_s24 as s24
import l2_fast
OUT=b.PROOFS/'s25'
b.ISOLATION='Reviewer guarantees isolation for S25; ps prohibited'
BASE=l2_fast.CACHE/'464197fa0ad748e84c636c4c78941c992d22bbb317337b7a2d7e03931039c943/libl2.dylib'

def monitor(stop):
 budget_root=b.PROOFS/'s25' if b.PROOFS/'s25' in OUT.parents else OUT
 start=json.loads((budget_root/'storage-live.jsonl').read_text().splitlines()[0])['time'] if (budget_root/'storage-live.jsonl').exists() else time.time()
 while not stop.is_set():
  paths=list(budget_root.rglob('*'))+list(l2_fast.CACHE.rglob('*'))
  size=sum(p.stat().st_size for p in paths if p.is_file() and not p.is_symlink() and (budget_root in p.parents or p.stat().st_mtime>=start))
  free=b.shutil.disk_usage(b.ROOT).free
  b.append(OUT/'budget.jsonl',dict(time=time.time(),new_evidence_and_cache_bytes=size,free_bytes=free))
  if size>100000000 or free<b.FLOOR:
   for proc in tuple(b.ACTIVE):proc.terminate()
   os._exit(3)
  stop.wait(5)

def partition(s,part=0,parts=100):
 roster=json.loads((b.PROOFS/'s21/roster-150.json').read_text());ids=(C.c_uint32*len(roster))(*roster);out=(l2_fast.Entry*10000)();n=C.c_size_t();counts=l2_fast.Counts()
 fn=s.lib.l2_enumerate;fn.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_size_t,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(l2_fast.Entry),C.POINTER(C.c_size_t),C.POINTER(l2_fast.Counts)]
 assert fn(s.table,ids,len(roster),10000,part,parts,1,out,C.byref(n),C.byref(counts))==0
 return dict(entries=[dict(indices=list(e.ids),score=e.score) for e in out[:n.value]],counts={key:getattr(counts,key) for key,_ in l2_fast.Counts._fields_})

def main():
 global OUT
 p=argparse.ArgumentParser();p.add_argument('action',choices=['trial','score','enumerate','wasm','verify','validate']);p.add_argument('--label',default='a');p.add_argument('--out',type=Path,default=OUT);a=p.parse_args();OUT=a.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
 cmd=['python3.12','-B','scripts/nikke_storage.py','storage-check','--required-bytes','100000000','--reserve-bytes',str(b.FLOOR)]
 r=subprocess.run(cmd,capture_output=True,text=True);b.append(OUT/'preflights.jsonl',dict(command=cmd,exit=r.returncode,stdout=r.stdout));assert not r.returncode
 stop=threading.Event();threading.Thread(target=monitor,args=(stop,),daemon=True).start()
 try:
  if a.action in ('verify','validate'):
   # The existing coordinator's complete acceptance commands, with a 100 MB budget above.
   (OUT/'tmp').mkdir(exist_ok=True)
   env=os.environ.copy();env.update(TMPDIR=str(OUT/'tmp'),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(b.PROOFS.parent/'pin-update-v1/validation-deps'),NIKKE_SLANG_ROOT=str(b.ROOT.parents[1]/'.tools/slang-2026.20-Darwin-arm64'))
   if a.action=='verify':jobs=[(v,['python3.12','-B',str(b.HERE/'l2_fast/verify.py'),'--full','--random','200000','--profiles',str(path),'--out',str(OUT/('parity-'+v))]) for v,path in s24.PATHS.items()]
   else:jobs=[('python',['python3.12','-m','unittest','discover','-s','tests']),('node',['node','--test',*[str(p.relative_to(b.ROOT)) for p in sorted((b.ROOT/'tests').glob('*.test.mjs'))]])]
   failed=[]
   for name,cmd in jobs:
    start=time.time()
    with (OUT/(a.action+'-'+name+'.log')).open('x') as f:
     proc=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT);b.ACTIVE.add(proc);rc=proc.wait();b.ACTIVE.discard(proc)
    b.append(OUT/(a.action+'.jsonl'),dict(name=name,command=cmd,exit=rc,seconds=time.time()-start));print(name,rc,flush=True)
    if rc:failed.append(name)
   if failed:raise RuntimeError('Failed acceptance jobs: '+', '.join(failed))
   return
  lib=l2_fast.build();receipt=OUT/(a.label+'-build.json')
  identity=dict(library=str(lib),sha256=hashlib.sha256(lib.read_bytes()).hexdigest())
  if receipt.exists():assert json.loads(receipt.read_text())==identity,'build identity changed; use a fresh label'
  else:b.save(receipt,identity)
  if a.action=='trial':
   (OUT/(a.label+'-l2.cpp')).write_bytes((b.HERE/'l2_fast/l2.cpp').read_bytes())
   for v in ['v3','v2']:
    rows=[]
    for tag,path in [('baseline',BASE),(a.label,lib)]:
     s=s24.load(v,path)
     for rep in range(3):
      before=b.gate(OUT);r=partition(s);after=b.observation();b.append(OUT/'trials.jsonl',dict(label=tag,version=v,repeat=rep,before=before,after=after,counts=r['counts']));print(tag,v,r['counts'],flush=True)
     rows.append(r)
    assert rows[0]['entries']==rows[1]['entries']
   return
  if a.action=='score':
   done={(r['version'],r['label'],r['count'],r['repeat']) for r in map(json.loads,(OUT/'scores.jsonl').read_text().splitlines())} if (OUT/'scores.jsonl').exists() else set()
   for v in s24.PATHS:
    for tag,path in [('baseline',BASE),('after',lib)]:
     s=s24.load(v,path)
     for count in [1000000,10000000]:
      for rep in range(3):
       if (v,tag,count,rep) in done:continue
       before=b.gate(OUT);r=b.benchmark.native(s,count,1,None);after=b.observation();b.append(OUT/'scores.jsonl',dict(version=v,label=tag,repeat=rep,before=before,after=after,**r));print(v,tag,count,r['kernel_ns_per_squad'],flush=True)
   return
  wasm=l2_fast.build(True) if a.action=='wasm' else None
  if wasm:
   receipt=OUT/'wasm-build.json';identity=dict(wasm=str(wasm),sha256=hashlib.sha256(wasm.read_bytes()).hexdigest())
   if receipt.exists():assert json.loads(receipt.read_text())==identity
   else:b.save(receipt,identity)
  for v,n,threads in ([('v3',150,10),('v3',206,10),('v2',150,10),('v3',150,7)] if a.action=='enumerate' else [('v3',150,10),('v3',206,10)]):
   s=s24.load(v,lib);rp=b.PROOFS/f's21/roster-{n}.json';table=OUT/(v+'.l2ft')
   if not table.exists():table.write_bytes(s.raw)
   for stride in ([1] if not wasm else ([100,20,1] if n==150 else [100,20])):
    for repeat in (range(3) if wasm and stride!=1 else [0]):
     job=f'{v}-{a.action}-{n}-{threads}-{stride}-{repeat}'
     if (OUT/(job+'.json')).exists():continue
     before=b.gate(OUT);start=time.perf_counter()
     r=b.node_result(['node',str(b.HERE/'l2_fast/runner.mjs'),'--enumerate','--wasm',str(wasm),'--table',str(table),'--roster',str(rp),'--workers',str(threads),'--stride',str(stride)]) if wasm else l2_fast.enumerate_top(s,json.loads(rp.read_text()),10000,threads,stride)
     after=b.observation();b.save(OUT/(job+'.json'),r);b.append(OUT/'enumerations.jsonl',dict(job=job,wall_seconds=time.perf_counter()-start,before=before,after=after,counts=r['counts'],partition_seconds=r.get('partition_seconds')));print(job,r['counts'],flush=True)
     if stride==1:
      ref=b.PROOFS/(f's22/search-cap/v3-{n}.json' if v=='v3' else f's21/native-{n}-15-10-1.json');x=json.loads(ref.read_text());assert len(r['entries'])==len(x['entries'])==10000
      assert all(u['indices']==w['indices'] and b.struct.pack('<d',u['score'])==b.struct.pack('<d',w['score']) for u,w in zip(r['entries'],x['entries']))
      assert all(r['counts'][k]==x['counts'][k] for k in ['visited','covered','scored']);b.save(OUT/(job+'-identity.json'),dict(reference=str(ref),entries=10000,differences=0,counts_identical=True))
 finally:stop.set()
if __name__=='__main__':main()
