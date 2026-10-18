"""Observe controller phase versus published charging flag inside CPU callbacks."""
import importlib.util,json,sys,hashlib
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('gauge_base',ROOT/'scripts/audit-burst-gauge.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from calculator.timeline import BurstController
from calculator.buff_manager import BuffManager

@contextmanager
def observe(owner):
 controllers=[];events=[];init=BurstController.__init__;notify=BuffManager.notify;add=BuffManager.add_burst_gauge
 def phase():return controllers[-1]._phase if controllers else None
 def construct(self,*args,**kw):init(self,*args,**kw);controllers.append(self)
 def event(self,event,t,caster=None,**kw):
  if caster==owner and event in ('battle_start','full_burst_start','full_burst_end','burst_enter:1'):
   events.append({'event':event,'time':t,'phase':phase(),'charging':self.state.get('burst_gauge_charging'),'gauge':self.state.get('burst_gauge')})
  return notify(self,event,t,caster,**kw)
 def charge(self,amount,t,*args,**kw):
  source=args[1] if len(args)>1 else kw.get('source','');before=self.state.get('burst_gauge',0);p=phase();charging=self.state.get('burst_gauge_charging');result=add(self,amount,t,*args,**kw)
  if source.startswith('charge_pct:'):events.append({'event':'instant_charge','source':source,'time':t,'phase':p,'charging':charging,'before':before,'after':self.state.get('burst_gauge'),'added':result})
  return result
 with patch.object(BurstController,'__init__',construct),patch.object(BuffManager,'notify',event),patch.object(BuffManager,'add_burst_gauge',charge):yield events

def main():
 cases=[];owner=base.c.NAMES[1]
 for mode in ('fixed','accumulate'):
  for timing in ('battle_start','burst_enter:1','full_burst_start','full_burst_end'):
   effects={owner:[base.c.E('boundary gauge charge','instant','burst_charge_pct',150,event=timing)]}
   with base.c.p.custom_effects(effects),base.configured(mode),observe(owner) as events:result=base.c.a.evaluate(base.c.body_for(base.c.NAMES,30,True))
   charges=[e for e in events if e['event']=='instant_charge'];cases.append({'mode':mode,'timing':timing,'authored_effects':effects,'events':events,'cpu_total':result['total_damage'],'burst_timeline':result['burst_timeline']})
   print(json.dumps({'mode':mode,'timing':timing,'charge_samples':charges[:2]},ensure_ascii=True),flush=True)
 files=['research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'cpu_reference_only':True,'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}}
 (ROOT/'research/detail-burst-gauge-boundary-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
