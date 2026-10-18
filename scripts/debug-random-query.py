"""Locate the first per-frame RNG disagreement; traces are oracle outputs only."""
import copy,importlib.util,json,random,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('debug_random',ROOT/'scripts/verify-random-target-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import run
from calculator.buff_manager import BuffManager
body=v.v.v.c.body_for(v.v.v.NAMES,5,True);body.update(seed=0,_debug_random_state=True)
effects={v.OWNER:dict(v.extra_cases())['caster-atk-special-lazy-target']}
observed=[];method=BuffManager._resolve_target
def target(self,rule,caster):
 result=method(self,rule,caster)
 if rule=='allies_random:2':observed.append({'time':self._cur_t,'caller':sys._getframe(1).f_code.co_name,'index':random.getstate()[1][-1],'targets':list(result)})
 return result
with v.v.v.c.p.custom_effects(effects):
 compiled=v.v.v.c.a.evaluate({**body,'_compile_gpu_detail':True})
 with patch.object(BuffManager,'_resolve_target',target):cpu=v.v.v.c.a.evaluate(body)
script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[0,0,5,i,0,-1,0,0] for i in range(5)];times=[];t=0
while t<=5:
 script.extend([[t,4,0,0,0,-1,0,0],[t,2,110,0,13,len(times),0,0]]);times.append(t);t+=1/60
device=v.v.v.c.Cuda()
try:result=run(device,[compiled['program']],script,[compiled['enemy']],[compiled['base_stats']],module_backend=sys.argv[1] if len(sys.argv)>1 else 'native',seeds=[0])
finally:device.close()
diff=[];at=0;current=624
for time,row in zip(times,result['queries'][0]):
 while at<len(observed) and observed[at]['time']<=time+1e-10:current=observed[at]['index'];at+=1
 if current!=int(row[0]):diff.append({'time':time,'cpu_index':current,'gpu_index':int(row[0]),'nearby':observed[max(0,at-4):at+3]})
report={'passed':not diff,'first_differences':diff[:4],'target_calls':len(observed),'cpu_total':cpu['total_damage'],'gpu_total':sum(result['totals'][0]),'cpu_observations':observed}
(ROOT/'research/detail-random-query-debug.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:x for k,x in report.items() if k!='cpu_observations'},ensure_ascii=True))
