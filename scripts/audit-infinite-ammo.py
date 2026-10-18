"""Independent CPU inputs/witnesses for the next infinite-ammo GPU port."""
import hashlib,importlib.util,json,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('ammo_control',ROOT/'scripts/verify-control-detail.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from calculator.timeline import CharState
from calculator.buff_manager import BuffManager

@contextmanager
def observe():
 states={};events={'cancel_reload':[],'ammo_consumed':{},'full_reload':{}}
 original_init=CharState.__init__;original_cancel=CharState._cancel_reload;original_notify=BuffManager.notify
 def init(self,*args,**kw):original_init(self,*args,**kw);states[self.name]=self
 def cancel(self,t,bm,*args,**kw):
  events['cancel_reload'].append({'name':self.name,'time':t,'ammo':self.ammo,'until':self.reloading_until})
  return original_cancel(self,t,bm,*args,**kw)
 def notify(self,event,t,caster=None,**kw):
  key={'squad_ammo_consume':'ammo_consumed','event:full_reload':'full_reload'}.get(event)
  if key:events[key][caster]=events[key].get(caster,0)+1
  return original_notify(self,event,t,caster,**kw)
 with patch.object(CharState,'__init__',init),patch.object(CharState,'_cancel_reload',cancel),patch.object(BuffManager,'notify',notify):yield states,events

def main():
 cases=[]
 for index in (0,2):
  name=c.NAMES[index]
  for forced in (False,True):
   effects=[c.E('one round','buff','max_ammo_flat',-10000),c.E('temporary infinite ammo','buff','infinite_ammo',0,event='every:1s',duration=.4,max_trigger=4)]
   if forced:effects.append(c.E('forced reload in infinite window','instant','force_reload',0,event='every:1.1s',max_trigger=3))
   body=c.body_for(c.NAMES,7,True)
   with c.p.custom_effects({name:effects}),observe() as (states,events):result=c.a.evaluate(body)
   subject=states[name]
   cases.append({'subject':name,'forced':forced,'input':body,'authored_effects':effects,'cpu_total':result['total_damage'],'events':events,'final_state':{'ammo':subject.ammo,'reloading_until':subject.reloading_until,'charge_phase':subject._charge_phase},'purpose':'CPU reference only; effect has no fixed_value in real definitions and must still be true'})
 source='research/upstream/nikke-calc-master/calculator/timeline.py'
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'cpu_reference_only':True,'gpu_implemented':False,'source_sha256':{source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()},'cases':cases,'semantics':['Presence boolean, not numeric fixed_value', 'Cancel active reload without completion or refill; retain ammo', 'Do not emit ammo consumption or last-bullet while infinite', 'Keep weapon-mode shot and bullet-duration counters firing', 'Revert to normal reload when the buff expires']}
 (ROOT/'research/detail-infinite-ammo-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'cases':len(cases),'cancellations':[len(x['events']['cancel_reload']) for x in cases]},ensure_ascii=True))
if __name__=='__main__':main()
