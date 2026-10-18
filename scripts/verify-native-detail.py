"""Compare native GPU code, portable GPU PTX and independent whole-squad CPU."""
import sys,json,hashlib,time,importlib.util
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for,a
from detail_gpu import evaluate_full
from gpu_selector import Cuda

def verify():
 scenarios=[('sg-clips-dual-muzzle',body_for(['리타','크라운','드레이크','크로우','메어리'],60,True)),('quincy-pellet-healing',body_for(['퀀시 : 이스케이프 퀸','루주','나가','모더니아','프로덕트 23'],60,True))]
 scenarios.append(('crown-auto-reload',json.loads((ROOT/'research/detail-crown-api-fixture.json').read_text(encoding='utf-8'))))
 scenarios.append(('kiri-three-defenders',json.loads((ROOT/'research/detail-kiri-api-fixture.json').read_text(encoding='utf-8'))))
 cases=[];periodic_results={};gauge_results={};damage_results={};d=Cuda()
 spec=importlib.util.spec_from_file_location('native_periodic',ROOT/'scripts/verify-periodic-detail.py');periodic=importlib.util.module_from_spec(spec);spec.loader.exec_module(periodic)
 spec=importlib.util.spec_from_file_location('native_gauge',ROOT/'scripts/verify-gauge-detail.py');gauge=importlib.util.module_from_spec(spec);spec.loader.exec_module(gauge)
 spec=importlib.util.spec_from_file_location('native_damage',ROOT/'scripts/verify-damage-detail.py');damage=importlib.util.module_from_spec(spec);spec.loader.exec_module(damage)
 try:
  results={}
  for backend in ('native','ptx'):
   for name,b in scenarios:
    c=a.evaluate({**b,'_compile_gpu_detail':True});result=evaluate_full(d,c,module_backend=backend);results[name,backend]=result
    print(json.dumps({'name':name,'module':result['compute']['module_backend'],'init_ms':result['compute']['initialization_ms'],'gpu_ms':result['compute']['elapsed_ms']},ensure_ascii=True),flush=True)
   periodic_results[backend]=periodic.verify(d,module_backend=backend)
   gauge_results[backend]=gauge.verify(d,module_backend=backend)
   damage_results[backend]=damage.verify(d,module_backend=backend)
  for name,b in scenarios:
   cpu=a.evaluate(b);native=results[name,'native'];ptx=results[name,'ptx'];keys=('total_damage','members','base_stats','burst_timeline')
   checks={k:cpu[k]==native[k]==ptx[k] for k in keys}
   cases.append({'name':name,'passed':all(checks.values()),'checks':checks,'total':cpu['total_damage'],'squad':b['squad'],'native_compute':native['compute'],'ptx_compute':ptx['compute']})
 finally:d.close()
 sources=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/gpu_selector.py']
 return {'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases) and all(r['passed'] for r in periodic_results.values()) and all(r['passed'] for r in gauge_results.values()) and all(r['passed'] for r in damage_results.values()),'damage_backends':damage_results,'periodic_backends':periodic_results,'gauge_backends':gauge_results,'device':d.name,'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
if __name__=='__main__':
 r=verify();(ROOT/'research/detail-native-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
