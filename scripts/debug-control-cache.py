"""Read-only differential trace for the same-frame camera cache boundary."""
import importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('control_debug',ROOT/'scripts/verify-control-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator.timeline import CharState
from calculator.buff_manager import BuffManager
from detail_gpu import run
label,effects,controls,camera,seconds,required=next(c for c in v.scenarios() if c[0].startswith('camera-switch-'));body=v.body_for(v.NAMES,seconds,True)
cpu_frames=[];calls=[];totals={n:0 for n in v.NAMES};original_tick=CharState.tick;original_get=BuffManager.get_buffs
def tick(self,t,bm,*args,**kw):
 hits=original_tick(self,t,bm,*args,**kw);totals[self.name]+=sum(h.damage for h in hits)
 if self.name==v.NAMES[-1]:cpu_frames.append({'t':t,'totals':[totals[n] for n in v.NAMES],'camera':list(bm.state.get('camera',()))})
 return hits
def get(self,who,target,t,*args,**kw):
 result=original_get(self,who,target,t,*args,**kw);calls.append({'t':t,'who':who,'camera':list(self.state.get('camera',())),'atk':result.get('atk_pct'),'version':[self._cache_version,self._value_version]});return result
with v.p.custom_effects(effects),v.configured(controls,camera):
 compiled=v.a.evaluate({**body,'_compile_gpu_detail':True})
 with patch.object(CharState,'tick',tick),patch.object(BuffManager,'get_buffs',get):cpu=v.a.evaluate(body)
script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[0,0,5,i,0,-1,0,0] for i in range(5)];t=0;frames=0
while t<=seconds:
 script.extend([[t,4,0,0,0,-1,0,0],[t,2,0,0,-1,frames,0,0]]);t+=1/60;frames+=1
d=v.Cuda()
try:gpu=run(d,[compiled['program']],script,[compiled['enemy']],[compiled['base_stats']],module_backend='native')
finally:d.close()
diffs=[];last=[0]*5
for i,(frame,g) in enumerate(zip(cpu_frames,gpu['queries'][0])):
 diff=[g[38+j]-frame['totals'][j] for j in range(5)]
 if diff!=last:diffs.append({'frame':i,**frame,'gpu':g[38:43],'diff':diff,'nearby_calls':[c for c in calls if abs(c['t']-frame['t'])<1e-8]});last=diff
report={'label':label,'diffs':diffs,'cpu_total':cpu['total_damage'],'gpu_totals':gpu['totals'][0],'frames':len(cpu_frames)}
(ROOT/'research/detail-control-cache-debug.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=True))
