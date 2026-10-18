"""CPU-only references for actual accumulated burst gauge; never shader inputs."""
import hashlib,importlib.util,json,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('gauge_control',ROOT/'scripts/verify-control-detail.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from calculator.buff_manager import BuffManager

@contextmanager
def configured(mode):
 original=c.a.sim.prepare;add=BuffManager.add_burst_gauge;observed={'calls':0,'changed':0,'ignored':0,'negative':0,'samples':[]};managers=[]
 def prepare(req):
  p=original(req);p.config['burst_gauge_mode']=mode;return p
 def charge(self,amount,t,*args,**kw):
  before=self.state.get('burst_gauge',0);result=add(self,amount,t,*args,**kw);after=self.state.get('burst_gauge',0)
  observed['calls']+=1;observed['changed']+=before!=after;observed['ignored']+=before==after;observed['negative']+=amount<0
  if len(observed['samples'])<24:observed['samples'].append({'time':t,'amount':amount,'before':before,'after':after,'charging':self.state.get('burst_gauge_charging')})
  if not managers:managers.append(self)
  return result
 with patch.object(c.a.sim,'prepare',prepare),patch.object(BuffManager,'add_burst_gauge',charge):yield observed,managers

def main():
 cases=[]
 for mode in ('fixed','accumulate'):
  for kind in ('baseline','caster-speed','initial-charge','negative-charge','charge-during-full-burst'):
   effects={}
   if kind=='caster-speed':effects={c.NAMES[1]:[c.E('caster gauge speed','buff','burst_charge_speed_pct',50,'all_allies')]}
   elif kind=='initial-charge':effects={c.NAMES[1]:[c.E('initial burst charge','instant','burst_charge_pct',150)]}
   elif kind=='negative-charge':effects={c.NAMES[1]:[c.E('negative burst charge','instant','burst_charge_pct',-20,event='every:1s')]}
   elif kind=='charge-during-full-burst':effects={c.NAMES[1]:[c.E('charge while full burst','instant','burst_charge_pct',100,event='every:1s',condition=['during_full_burst'])]}
   body=c.body_for(c.NAMES,30,True)
   with c.p.custom_effects(effects),configured(mode) as (events,managers):result=c.a.evaluate(body)
   cases.append({'name':mode+'-'+kind,'input':body,'config_override':{'burst_gauge_mode':mode},'authored_effects':effects,'cpu_total':result['total_damage'],'burst_timeline':result['burst_timeline'],'events':events,'final_gauge':managers[0].state.get('burst_gauge') if managers else None})
 source=['research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'cpu_reference_only':True,'gpu_implemented':False,'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in source},'required_gpu_work':['Fixed/accumulate controller mode and live gauge clamping/gates','Weapon and mode energy, pellets/muzzles and camera-qualified full charge gain','Caster raw/landed reference conversion for speed buffs','Instant charge, skill hit exceptions and event order']}
 (ROOT/'research/detail-burst-gauge-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'cases':len(cases),'changed':[r['events']['changed'] for r in cases],'first_stage_times':[next((e['time'] for e in r['burst_timeline'] if e['character']),None) for r in cases]},ensure_ascii=True))
if __name__=='__main__':main()
