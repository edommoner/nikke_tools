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
