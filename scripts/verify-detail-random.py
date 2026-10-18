"""Check actual GPU draws against CPython; never upload reference draws."""
import array,ctypes as C,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from gpu_selector import Cuda

def plans_for(case):
 return ([[0,32,0] for _ in case['words']]
         +[[0,row['bits'],0] for row in case['bits']]
         +[[1,row['n'],0] for row in case['below']]
         +[[2,len(row['pool']),row['k']] for row in case['samples']])

def expected_for(case):
 rows=[[v] for v in case['words']]+[[r['value']] for r in case['bits']]+[[r['value']] for r in case['below']]+[r['result'] for r in case['samples']]
 return [v for row in rows for v in row+[0xffffffff]*(5-len(row))]

def verify():
 references=json.loads((ROOT/'research/detail-python-random-cpu-references.json').read_text(encoding='utf-8'))['cases']
 plans=plans_for(references[0]);assert all(plans_for(c)==plans for c in references)
 assert all(len(c['initial_state'])==625 and len(c['final_state'])==625 for c in references)
 n=len(references);count=len(plans)
 if '--prepare-only' in sys.argv:
  print(json.dumps({'seeds':n,'operations_per_seed':count,'gpu_run':False,'uploaded_oracle_outputs':False}));return
 source=ROOT/'research/ports/detail_random.cu';ptx=source.with_suffix('.ptx');manifest=json.loads(source.with_suffix('.json').read_text(encoding='utf-8'))
 assert manifest['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
 assert manifest['ptx_sha256']==hashlib.sha256(ptx.read_bytes()).hexdigest()
 initial=array.array('I',[v for c in references for v in c['initial_state']]);control=array.array('i',[v for row in plans for v in row])
 output=array.array('I',[0])*(n*count*5);final=array.array('I',[0])*(n*625);status=array.array('i',[0])*n
 assert initial.itemsize==4 and control.itemsize==4
 d=Cuda()
 try:
  module=C.c_void_p();blob=ptx.read_bytes()+b'\0';d.call('cuModuleLoadData',C.byref(module),C.cast(C.c_char_p(blob),C.c_void_p))
  function=C.c_void_p();d.call('cuModuleGetFunction',C.byref(function),module,b'random_primitives')
  # These are the only uploads: initial state, authored operations, empty outputs.
  pi=d.upload(initial);pc=d.upload(control);po=d.upload(output);pf=d.upload(final);ps=d.upload(status)
  args=[pi,pc,C.c_int(count),C.c_int(n),po,pf,ps];params=(C.c_void_p*len(args))(*(C.cast(C.byref(v),C.c_void_p) for v in args))
  d.call('cuLaunchKernel',function,1,1,1,32,1,1,0,None,params,None);d.call('cuCtxSynchronize')
  for target,ptr in [(output,po),(final,pf),(status,ps)]:
   buf=(C.c_char*(len(target)*target.itemsize)).from_buffer(target);d.call('cuMemcpyDtoH_v2',C.cast(buf,C.c_void_p),ptr,len(target)*target.itemsize)
  rows=[]
  for i,case in enumerate(references):
   got=list(output[i*count*5:(i+1)*count*5]);want=expected_for(case)
   checks={'draws_and_ordered_samples':got==want,'final_MT_state':list(final[i*625:(i+1)*625])==case['final_state'],'status':status[i]==0}
   row={'seed':case['seed'],'passed':all(checks.values()),'checks':checks,'operations':count}
   if got!=want:row['first_mismatch']=next({'offset':j,'operation':j//5,'gpu':a,'cpu':b} for j,(a,b) in enumerate(zip(got,want)) if a!=b)
   rows.append(row);print(json.dumps(row),flush=True)
 finally:d.close()
 files=['research/ports/detail_random.cu','research/ports/detail_random.ptx','research/ports/detail_random.json','scripts/build-detail-random.py','scripts/verify-detail-random.py','research/detail-python-random-cpu-references.json','app/gpu_selector.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(r['passed'] for r in rows),'combat_integrated':False,'cpu_trace_used_as_gpu_input':False,'oracle_draws_uploaded':False,'cases':rows,'scope':'MT words, getrandbits<=32, small-pool rejection and ordered sample, including twist boundaries; no gameplay random-target parity claim yet','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-random-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':verify()
