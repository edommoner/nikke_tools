"""Read actual native gauge dictionaries and saved GPU banks; no GPU/build calls."""
import array,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from portable_specs import LIMITS as L
from portable_resource_decode import resource_readback

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def witness(names,resource_names,run):
 seen=[];original=timeline.BurstController.tick
 def tick(controller,t,bm,state):
  seen[:]=[bm.state];return original(controller,t,bm,state)
 with patch.object(timeline.BurstController,'tick',tick):run()
 assert seen
 gauges=seen[0].get('gauges',{});rows=[]
 for n in names:
  values=gauges.get(n,{})
  rows.append({key:dict(present=key in values,value=values.get(key,0.0),cap_present='_gauge_max:'+key in values,base_cap=values.get('_gauge_max:'+key)) for key in resource_names})
 return rows
