"""Isolate the failed catalog batch with one independent thread per block."""
import ctypes as C,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('batch_probe',ROOT/'scripts/verify-catalog-batch-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
old=json.loads((ROOT/'research/detail-catalog-batch-verification.json').read_text(encoding='utf-8'))
names=[c['character'] for c in old['cases'][8:16]];items=[]
for name in names:
    squad=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4]
    body=v.body_for(squad,30,True);body.update(seed=12345,shooting_policy='auto',burst_policy='rules',burst_gauge_mode='fixed',_debug_random_state=True)
    items.append((name,body,v.a.evaluate({**body,'_compile_gpu_detail':True})))
device=v.Cuda();real=device.lib.cuCtxSetLimit;real.argtypes=[C.c_int,C.c_size_t];real.restype=C.c_int
def larger(kind,size):return real(kind,max(size,262144))
original_call=device.call
def launch(name,*args):
    if name=='cuLaunchKernel':
        args=list(args);args[1]=len(items);args[4]=1
    return original_call(name,*args)
device.call=launch
try:
    rows=v.evaluate_batch(device,items,'native');report=dict(passed=all(r['passed'] for r in rows),cuda_error=None,cases=rows)
except Exception as error:report=dict(passed=False,cuda_error=str(error),cases=[])
finally:device.close()
report['launch']='one thread per block; original stack limit'
report['source_sha256']={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin']}
(ROOT/'research/detail-immunity-launch-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=report['passed'],cuda_error=report['cuda_error']),ensure_ascii=True),flush=True)
