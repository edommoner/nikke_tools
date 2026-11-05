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
