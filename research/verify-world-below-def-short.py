"""Final-defense selection and native oracle for both GPUs."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('below_def_base',ROOT/'research/verify-world-duration-scaling-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_below_def_cases import fixtures
from portable_below_def_contracts import verify
from world_below_def_native import observe
from portable_specs import LIMITS as L

def prepare():
    entries=[]
    for c in fixtures():
        w,m,p=suite.compile_case(c);entries.append((c['name'],w,(c,m,p)))
    seed=entries[0][1];at=L['RECIPIENT_BASE']+8
    assert seed[at]==14
    for label,offset,value in [('count',1,1),('mask',2,1),('exclude',3,1),('order',4,1),('state',5,1),('reserved',7,8),('lazy-overflow',7,257<<4),('stat-key',6,256)]:
        w=list(seed);assert w[at+offset]!=value;w[at+offset]=value;entries.append(('reject/below-def-'+label,w,None))
    data=array.array('I',[len(entries)])
    for _,w,_ in entries:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return entries,data.tobytes()

def native_reference(domain):
    n,t=observe(domain[0]);verify(domain[0],n);n.pop('below_def_selections');return dict(battle=n,skill_trace=t)

def compare(block,domain):
    c,m,p=domain;expected=native_reference(domain);actual=suite.decoded(block,m,c,p)
    if c.get('observe_healing_storage'):actual['healing_storage']=base.base.storage.decoded_storage(block,m,c)
    changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]]
    assert block[0]==0 and not changed,(c['name'],block[0],changed)
    assert suite.reload.charge.team.skill_trace(block,m)==expected['skill_trace'],(c['name'],'full skill trace')
    return expected

def validate_rejection(block,name):assert name.startswith('reject/below-def-') and block[0]==64
