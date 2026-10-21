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

def main():
 import portable_backend
 def forbidden(*a,**k):raise AssertionError('GPU/build forbidden in resource witness')
 suite=module('projectile_resource_suite','research/verify-world-projectile.py');real=module('projectile_real_resource','research/verify-world-projectile-rosters.py');rows,programs,bad=suite.prepare();cases=[]
 with patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden),patch.object(suite,'execute',forbidden):
  for domain,report,items in [('literal',json.loads((ROOT/'research/portable-world-projectile-metal.json').read_text()),[(c,(w,m,b)) for c,(w,m,b) in zip(rows,programs)]),('real',json.loads((ROOT/'research/portable-world-projectile-rosters-metal.json').read_text()),[(c,(p,w,m)) for c,p,w,m in real.prepare()])]:
   raw=Path(report['captured'],'readback.bin').read_bytes();ow=786432*4
   for i,(c,packed) in enumerate(items):
    if domain=='literal':w,m,b=packed;names=m['names'];run=lambda c=c:suite.inspect_native(c)
    else:p,w,m=packed;names=c['body']['squad'];run=lambda c=c:real.native_reference(c['body'])
    keys=m['resource_names']
    if not keys:continue
    words=array.array('I');words.frombytes(raw[i*ow:(i+1)*ow]);assert words[0]==0
    number=lambda at:struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0]
    actual=resource_readback(words,m,L,number)['resources'];native=witness(names,keys,run);assert actual==native,(domain,c,actual,native)
    cases.append(dict(domain=domain,index=i,name=c.get('name',c.get('character')),duration=c.get('duration'),resource_names=keys,gpu=actual,native=native,passed=True))
 result=dict(passed=True,cases=cases,checked_battles=len(cases),checked_owner_resource_entries=sum(len(c['resource_names'])*5 for c in cases),canonical_quantities_modified=False,gpu_calls=0,build_calls=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-projectile-resource-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('Saved gauge value/cap/presence native audit',len(cases),'battles;GPU0')
if __name__=='__main__':main()
