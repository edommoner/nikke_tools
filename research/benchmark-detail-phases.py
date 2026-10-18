"""Isolated detailed-GPU baseline without changing production code.

Driver calls are timed on the host; timing-enabled CUDA events surround only the
detail launch. Identical batch members verify separate workspaces and outputs.
No CPU battle trace, coarse formula or result cache feeds the GPU.
"""
import argparse,copy,ctypes as C,hashlib,json,statistics,sys,time
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter,detail_gpu as g
from gpu_selector import Cuda
from detail_coverage import body_for

class DriverProfile:
 def __init__(self,device):
  self.device=device;self.original=device.call;self.begin=C.c_void_p();self.end=C.c_void_p()
  signatures={'cuEventCreate':[C.POINTER(C.c_void_p),C.c_uint],
   'cuEventRecord':[C.c_void_p,C.c_void_p],'cuEventElapsedTime':[C.POINTER(C.c_float),C.c_void_p,C.c_void_p],
   'cuEventDestroy_v2':[C.c_void_p],'cuFuncGetAttribute':[C.POINTER(C.c_int),C.c_int,C.c_void_p]}
  for name,args in signatures.items():
   fn=getattr(device.lib,name);fn.argtypes=args;fn.restype=C.c_int
  self.original('cuEventCreate',C.byref(self.begin),0);self.original('cuEventCreate',C.byref(self.end),0)
  self.device.call=self.call;self.reset()
 def reset(self):self.calls=defaultdict(lambda:dict(count=0,host_ms=0.0,bytes=0));self.launches=0
 def call(self,name,*args):
  launch=name=='cuLaunchKernel'
  if launch:self.original('cuEventRecord',self.begin,None)
  start=time.perf_counter()
  try:return self.original(name,*args)
  finally:
   row=self.calls[name];row['count']+=1;row['host_ms']+=(time.perf_counter()-start)*1000
   if name in ('cuMemcpyHtoD_v2','cuMemcpyDtoH_v2'):row['bytes']+=int(args[2])
   if name=='cuMemAlloc_v2':row['bytes']+=int(args[1])
   if launch:self.original('cuEventRecord',self.end,None);self.launches+=1
 def finish(self):
  assert self.launches==1,'One complete detail launch per observation'
  elapsed=C.c_float();self.original('cuEventElapsedTime',C.byref(elapsed),self.begin,self.end)
  return dict(kernel_device_ms=float(elapsed.value),driver_calls={name:dict(row,host_ms=round(row['host_ms'],4)) for name,row in self.calls.items()})
 def attributes(self):
  fn=self.device._detail_cached_module[3];result={}
  for name,code in (('max_threads_per_block',0),('shared_bytes_per_block',1),('local_bytes_per_thread',3),('registers_per_thread',4)):
   value=C.c_int();self.original('cuFuncGetAttribute',C.byref(value),code,fn);result[name]=value.value
  return result
 def close(self):
  self.device.call=self.original
  for event in (self.begin,self.end):self.original('cuEventDestroy_v2',event)

def inputs():
 yield 'standard-damage',body_for(['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'],duration=30)
 raw=json.loads((ROOT/'research/base-copy-api-fixtures.json').read_text(encoding='utf-8'))
 yield 'base-copy',next(row['evaluation'] for row in raw if row['name']=='raw-copy-combined')
 yield 'owned-recovery',json.loads((ROOT/'research/detail-heal-charge-api-fixture.json').read_text(encoding='utf-8'))

def signature(payload):
 return hashlib.sha256(json.dumps({k:payload[k] for k in ('total_damage','members','base_stats','burst_timeline')},sort_keys=True,ensure_ascii=True).encode()).hexdigest()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--repeats',type=int,default=3);parser.add_argument('--batches',default='1,8,32');args=parser.parse_args()
 batches=[int(n) for n in args.batches.split(',')];assert 1 in batches and all(1<=n<=64 for n in batches) and 1<=args.repeats<=10
 baseline=json.loads((ROOT/'research/carrier-checkpoint.json').read_text(encoding='utf-8'));assert baseline['passed']
 files=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]+list((ROOT/'app').glob('detail_effects*'))+[Path(__file__)]
 hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
 for path,digest in baseline['source_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
 started=time.perf_counter();device=Cuda();context_ms=(time.perf_counter()-started)*1000;profile=DriverProfile(device);rows=[];summaries=[];attributes=None
 original_run=g.run
 try:
  for name,source in inputs():
   body={k:copy.deepcopy(v) for k,v in source.items() if not k.startswith('_debug')};body.pop('compute_backend',None);body.pop('verify_detail',None)
   expected=None
   for batch in batches:
    for sample in range(args.repeats+(1 if batch==1 else 0)):
     cold=not rows;warmup=batch==1 and sample==0
     mark=time.perf_counter();compiled=adapter.evaluate({**body,'_compile_gpu_detail':True});prepare_ms=(time.perf_counter()-mark)*1000
     observed={}
     def run(device,programs,script,enemies,base_stats,module_backend='auto',seeds=None):
      assert len(programs)==len(enemies)==len(base_stats)==1
      seed=seeds[0] if seeds is not None else 0
      result=original_run(device,programs*batch,script,enemies*batch,base_stats*batch,module_backend='native',seeds=[seed]*batch)
      assert all(query==result['queries'][0] for query in result['queries'])
      assert all(total==result['totals'][0] for total in result['totals'])
      observed.update(batch_outputs_identical=True,workspace_bytes=result['workspace_bytes'],script_steps=len(script),query_rows=len(result['queries'][0]))
      return result
     profile.reset();mark=time.perf_counter()
     with patch.object(g,'run',run):payload=g.evaluate_full(device,compiled,module_backend='native')
     wall_ms=(time.perf_counter()-mark)*1000;metrics=profile.finish();actual=signature(payload)
     if expected is None:expected=actual
     assert actual==expected,'Repeated/batched simulation changed detailed output'
     assert payload['compute']['backend']=='cuda_detail' and observed['workspace_bytes']==batch*1103888
     if attributes is None:attributes=profile.attributes()
     row=dict(case=name,batch=batch,sample=sample,warmup=warmup,cold_module=cold,prepare_ms=round(prepare_ms,4),evaluate_wall_ms=round(wall_ms,4),request_ms=round(prepare_ms+wall_ms,4),initialization_ms=payload['compute']['initialization_ms'],reported_elapsed_ms=payload['compute']['elapsed_ms'],result_signature=actual,**observed,**metrics)
     rows.append(row);print(json.dumps(dict(case=name,batch=batch,sample=sample,warmup=warmup,kernel_device_ms=round(metrics['kernel_device_ms'],3),evaluate_wall_ms=row['evaluate_wall_ms'])),flush=True)
    chosen=[r for r in rows if r['case']==name and r['batch']==batch and not r['warmup']]
    med=lambda key:round(statistics.median(r[key] for r in chosen),4)
    summaries.append(dict(case=name,batch=batch,samples=len(chosen),kernel_median_ms=med('kernel_device_ms'),evaluate_median_ms=med('evaluate_wall_ms'),request_median_ms=med('request_ms'),prepare_median_ms=med('prepare_ms'),kernel_min_ms=min(r['kernel_device_ms'] for r in chosen),kernel_max_ms=max(r['kernel_device_ms'] for r in chosen),squads_per_second=round(batch*1000/med('evaluate_wall_ms'),3)))
 finally:profile.close();device.close()
 stable=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest for p,digest in hashes.items())
 report=dict(passed=stable,scope='Baseline measurement, no production optimization yet. Homogeneous candidate batches, one thread/block/squad, no CPU battle simulation or trace replay.',device=device.name,abi=g.DETAIL_ABI,context_creation_ms=round(context_ms,4),function_attributes=attributes,repeats=args.repeats,batches=batches,results=rows,summary=summaries,source_stable=stable,source_sha256=hashes,correctness='Repeated outputs and all batched outputs match the corresponding single-squad signature. Existing v48 regression is a separate archived correctness baseline.',measurement_references='research/performance-measurement-references.json')
 (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');assert stable

if __name__=='__main__':main()
