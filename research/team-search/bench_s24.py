"""S24 sequential coordinator; uses the S23 gate, workloads and storage monitor."""
import argparse, ctypes as C, hashlib, itertools, json, os, subprocess, threading, time
from pathlib import Path
import bench_s23 as b
import l2_fast
OUT=b.PROOFS/'s24'
b.ISOLATION='Reviewer guarantees no other jobs on this Mac; process isolation confirmed by reviewer (S24 brief); ps prohibited'
PATHS={'v1':b.PROOFS/'s18/profiles.json','v2':b.PROOFS/'s20/dev/final-profiles.json','v3':b.PROOFS/'s22/final-profiles.json'}

def load(v,lib):
 s=l2_fast.Score.load(PATHS[v],library=lib)
 s.lib.l2_generate.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32),C.c_size_t,C.c_int];s.lib.l2_generate.restype=C.c_uint32
 return s

def trial(label):
 lib=Path(json.loads((OUT/'baseline/build.json').read_text())['library']) if label=='baseline-trial' else l2_fast.build();d=OUT/label;d.mkdir(exist_ok=True)
 (d/'l2.cpp').write_bytes((OUT/'baseline-l2.cpp').read_bytes() if label=='baseline-trial' else (b.HERE/'l2_fast/l2.cpp').read_bytes())
 b.save(d/'build.json',{'library':str(lib)})
 oldlib=Path(json.loads((OUT/'baseline/build.json').read_text())['library'])
 for v in PATHS:
  s=load(v,lib);old=load(v,oldlib);ids=(C.c_uint32*(8192*5))();seed=190019
  for _ in range(16):
   seed=s.lib.l2_generate(s.table,seed,ids,8192,1);x,y=s.score_indices(ids,True);u,w=old.score_indices(ids,True)
   assert bytes(x)==bytes(u) and bytes(y)==bytes(w),(label,v)
  b.append(OUT/'candidate-parity.jsonl',dict(candidate=label,version=v,squads=131072,raw_values=786432,differences=0))
  for repeat in range(3):
   before=b.gate(OUT);r=b.benchmark.native(s,1000000,1,None);after=b.observation()
   b.append(OUT/'candidates.jsonl',dict(candidate=label,version=v,repeat=repeat,before=before,after=after,**r));print(label,v,r['kernel_ns_per_squad'],flush=True)

def main():
 global OUT
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','trial','measure','enumerate','wasm-enumerate','verify','validate']);p.add_argument('--label',default='a');p.add_argument('--out',type=Path,default=OUT);a=p.parse_args();OUT=a.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
 cmd=['python3.12','-B',str(b.ROOT/'scripts/nikke_storage.py'),'storage-check','--required-bytes',str(300*1024**2),'--reserve-bytes',str(b.FLOOR)]
 r=subprocess.run(cmd,capture_output=True,text=True);b.append(OUT/'storage-preflights.jsonl',dict(command=cmd,exit=r.returncode,stdout=r.stdout,stderr=r.stderr));assert not r.returncode
 stop=threading.Event();threading.Thread(target=b.monitor,args=(OUT,stop),daemon=True).start()
 try:
  if a.action=='prepare':
   d=OUT/'baseline';d.mkdir(exist_ok=True)
   if not (OUT/'baseline-l2.cpp').exists():(OUT/'baseline-l2.cpp').write_bytes(subprocess.check_output(['git','show','2e720e15:research/team-search/l2_fast/l2.cpp'],cwd=b.ROOT))
   for f in ('l2.cpp','l2.h','cli.cpp'):
    (d/f).write_bytes((OUT/'baseline-l2.cpp').read_bytes() if f=='l2.cpp' else subprocess.check_output(['git','show',f'2e720e15:research/team-search/l2_fast/{f}'],cwd=b.ROOT))
   lib=d/'libl2.dylib';subprocess.run(['clang++',*l2_fast.FLAGS,str(d/'l2.cpp'),'-shared','-fPIC','-o',str(lib)],check=True);b.save(d/'build.json',dict(library=str(lib)))
  elif a.action=='trial':trial(a.label)
  elif a.action in ('verify','validate'):
   env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(b.PROOFS.parent/'pin-update-v1/validation-deps'),NIKKE_SLANG_ROOT='/Users/edo/Documents/ChatGPT/nikke_tools/.tools/slang-2026.20-Darwin-arm64')
   if a.action=='verify':commands=[(v,['python3.12','-B',str(b.HERE/'l2_fast/verify.py'),'--full','--random','200000','--profiles',str(path),'--out',str(OUT/('parity-'+v))]) for v,path in PATHS.items()]
   else:commands=[('python',['python3.12','-m','unittest','discover','-s','tests']),('node',['node','--test',*[str(p.relative_to(b.ROOT)) for p in sorted((b.ROOT/'tests').glob('*.test.mjs'))]])]
   for name,cmd in commands:
    start=time.time()
    with (OUT/(a.action+'-'+name+'.log')).open('x') as f:
     proc=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT);b.ACTIVE.add(proc)
     try:rc=proc.wait()
     finally:b.ACTIVE.discard(proc)
    b.append(OUT/(a.action+'.jsonl'),dict(name=name,command=cmd,exit=rc,seconds=time.time()-start));print(name,rc,flush=True)
  else:measure(a.action)
 finally:stop.set()

def measure(action):
 lib=l2_fast.build();wasm=l2_fast.build(True)
 identity=dict(native_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),wasm_sha256=hashlib.sha256(wasm.read_bytes()).hexdigest(),profiles={v:hashlib.sha256(p.read_bytes()).hexdigest() for v,p in PATHS.items()})
 receipt=OUT/'measurement-build.json'
 if receipt.exists():
  if json.loads(receipt.read_text())!=identity:raise RuntimeError('Measurement identity changed; preserve existing evidence and use a fresh destination')
 else:
  if (OUT/'runs.jsonl').exists():
   previous=json.loads((OUT/'environment.json').read_text())
   assert previous['native_build']['outputs'][lib.name]==identity['native_sha256']
   assert previous['wasm_build']['outputs']['l2.wasm']==identity['wasm_sha256']
  b.save(receipt,identity)
 done={json.loads(l)['job'] for l in (OUT/'runs.jsonl').read_text().splitlines()} if (OUT/'runs.jsonl').exists() else set()
 for v in PATHS:
  s=load(v,lib);table=OUT/(v+'.l2ft');table.write_bytes(s.raw)
  s9=[r['members'] for r in map(json.loads,(b.HERE/'s9-dataset.jsonl').read_text().splitlines()) if r['backend']=='native_detail' and r.get('total_damage',0)>0]
  roster=b.random.Random(190150).sample(s.names,150);family=[roster[:3]+list(pair) for pair in itertools.permutations(roster[3:],2)]
  if action=='measure':
   for engine in (['native','WASM'] if v=='v3' else ['native']):
    for workload,rows,count in ([('random',None,10000000),('S9',s9,len(s9)),('family',family,len(family))] if v=='v3' else [('random',None,10000000)]):
     inp=OUT/(workload+'.u32')
     if rows and not inp.exists():inp.write_bytes(bytes(s._indices(rows)))
     for workers in ([1,10] if v=='v3' else [1]):
      for repeat in range(3):
       job=f'{v}-{engine}-{workload}-{workers}-{repeat}'
       if job in done:continue
       before=b.gate(OUT)
       if engine=='native':r=b.benchmark.native(s,count,workers,rows)
       else:r=b.node_result(['node',str(b.HERE/'l2_fast/runner.mjs'),'--bench','--wasm',str(wasm),'--table',str(table),'--workers',str(workers),'--count',str(count)]+(['--input',str(inp)] if rows else []))
       after=b.observation();b.append(OUT/'runs.jsonl',dict(job=job,version=v,engine=engine,workload=workload,repeat=repeat,before=before,after=after,**r));print(job,r['kernel_ns_per_squad'],flush=True)
  elif v!='v1':
   for n in ([150,206] if v=='v3' else [150]):
    if action=='wasm-enumerate' and v!='v3':continue
    for stride in ([100,20] if action=='wasm-enumerate' else [1]):
     for repeat in (range(3) if action=='wasm-enumerate' else [0]):
      job=f'{v}-{action}-{n}-{stride}-{repeat}'
      if job in done:continue
      rp=b.PROOFS/f's21/roster-{n}.json';before=b.gate(OUT);start=time.perf_counter()
      if action=='enumerate':r=l2_fast.enumerate_top(s,json.loads(rp.read_text()),10000,10,stride)
      else:r=b.node_result(['node',str(b.HERE/'l2_fast/runner.mjs'),'--enumerate','--wasm',str(wasm),'--table',str(table),'--roster',str(rp),'--workers','10','--stride',str(stride)])
      wall=time.perf_counter()-start;after=b.observation();b.save(OUT/(job+'.json'),r)
      b.append(OUT/'runs.jsonl',dict(job=job,version=v,n=n,stride=stride,repeat=repeat,wall_seconds=wall,counts=r['counts'],before=before,after=after));print(job,wall,flush=True)
      if action=='enumerate':
       ref=b.PROOFS/(f's22/search-cap/v3-{n}.json' if v=='v3' else f's21/native-{n}-15-10-1.json');x=json.loads(ref.read_text());assert len(r['entries'])==len(x['entries'])==10000
       assert all(u['indices']==w['indices'] and b.struct.pack('<d',u['score'])==b.struct.pack('<d',w['score']) for u,w in zip(r['entries'],x['entries']))
       assert all(r['counts'][k]==x['counts'][k] for k in ('visited','covered','scored'));b.save(OUT/(job+'-identity.json'),dict(reference=str(ref),differences=0,entries=10000,counts_identical=True))
if __name__=='__main__':main()
