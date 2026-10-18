"""Matched and mismatched real enemy-code branches; CPU observations are output."""
import sys,json,hashlib,importlib.util
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda
from detail_coverage import body_for
spec=importlib.util.spec_from_file_location('code_predicates_oracle',ROOT/'scripts/verify-predicates-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator.buff_manager import BuffManager

def verify(device):
 original=BuffManager._condition_ok;cases=[]
 for backend in ('native','ptx'):
  for name,wanted in [('브리드 : 사일런트 트랙','풍압'),('헬름 : 아쿠아마린','전격'),('마르차나 : 마린 스터디','전격')]:
   for code in ('풍압','전격'):
    observed={'passed':0,'failed':0}
    def tracked(manager,conditions,caster,t,eff=None):
     result=original(manager,conditions,caster,t,eff)
     if caster==name and any(c.startswith('target_code:') for c in conditions):observed['passed' if result else 'failed']+=1
     return result
    names=[name]+[n for n in v.NAMES if n!=name][:4];body=body_for(names,60,True);body['enemy']['code']=code
    with patch.object(BuffManager,'_condition_ok',tracked):case=v.periodic.full.compare(device,'real-code-'+name+'-'+code,body,module_backend=backend)
    case['cpu_condition_observations']=observed;case['enemy_code']=code;case['backend']=backend
    exercised=observed['passed']>0 if code==wanted else observed['failed']>0 and observed['passed']==0
    case['code_branch_exercised']=exercised;case['passed'] &= exercised;cases.append(case)
    print(json.dumps({'name':name,'enemy_code':code,'backend':backend,'passed':case['passed'],'observed':observed,'total':case['gpu_total']},ensure_ascii=True),flush=True)
 return cases

if __name__=='__main__':
 device=Cuda()
 try:cases=verify(device)
 finally:device.close()
 files=['scripts/verify-enemy-codes-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/engine_worker.py','app/engine_compat.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'cases':cases,'scope':'three real characters, two enemy elements, native/PTX in fixed 60-second grown static-boss squads','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-enemy-codes-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
