"""Run stage112 and A-stage32 with one context; independent CPU comparisons."""
import hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=module('stage_suite_main','scripts/verify-burst-stage-detail.py')
a=module('stage_suite_extra','scripts/verify-all-stage-detail.py')
def save(path,cases,extra=False):
 files=['scripts/verify-burst-stage-suite.py','scripts/verify-burst-stage-detail.py','scripts/verify-all-stage-detail.py','scripts/verify-control-detail.py','scripts/verify-periodic-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(r['passed'] for r in cases),'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 if extra:report['scope']='Synthetic complete raw effect replacement for A-stage selection; not full real Red Hood skill parity'
 (ROOT/path).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return report['passed']
if __name__=='__main__':
 main=[];extra=[];d=v.c.Cuda()
 try:
  for backend in ('native','ptx'):
   main+=v.verify(d,backend);extra+=a.run(d,backend)
 finally:d.close()
 ok=save('research/detail-burst-stage-verification.json',main)
 ok=save('research/detail-all-stage-verification.json',extra,True) and ok
 assert len(main)==112 and len(extra)==32
 raise SystemExit(0 if ok else 1)
