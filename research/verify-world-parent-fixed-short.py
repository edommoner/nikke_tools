"""One CPU/CUDA/Metal table for parent fixed quantities and malformed tags."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('parent_fixed_base',ROOT/'research/verify-world-full-burst-query-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
suite,cross=prior.suite,prior.cross
from portable_parent_fixed_cases import fixtures
from portable_parent_fixed_contracts import verify
from world_parent_fixed_native import observe
from portable_specs import LIMITS as L,FIELDS as F

def prepare():
    rows=[]
    for c in fixtures():
        w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    seed=rows[0][1];row=1;at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];packet=L['DAMAGE_DEFINITION_BASE']+row*8
    for name,offset,value in [('mixed-flags',at+F['DAMAGE_FLAGS'],262144|64),('two-hits',packet+2,2),('normal-formula',packet+3,1),('pending',packet+6,1),('gauge',packet+5,0x3ff00000),('HP-mode',L['MODE_BASE']+row*L['MODE_WORDS']+20,0x48504231),('periodic-interval',at+F['INTERVAL']+1,0x3ff00000)]:
        w=list(seed);assert w[offset]!=value;w[offset]=value;rows.append(('reject/parent-fixed-'+name,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,t=observe(domain[0]);verify(domain[0],n);n.pop('parent_fixed');return dict(battle=n,skill_trace=t)
def compare(block,domain):return prior.landing.base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/parent-fixed-') and block[0]==64,(name,block[0])
