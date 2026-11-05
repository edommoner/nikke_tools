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
