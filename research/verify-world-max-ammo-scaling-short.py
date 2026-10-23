"""One native/CUDA/Metal table for live recipient capacity scaling."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('max_ammo_parent',ROOT/'research/verify-world-parent-fixed-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
suite,cross=prior.suite,prior.cross
from portable_max_ammo_scaling_cases import fixtures
from portable_max_ammo_scaling_contracts import verify
from world_max_ammo_scaling_native import observe
from portable_specs import LIMITS as L,FIELDS as F,STATS
def prepare():
    rows=[]
    for c in fixtures():
        w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    seed=rows[0][1];row=1;at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
    changes=[('wrong-stat',at+F['STAT'],STATS['atk_pct']),('wrong-kind',at+F['KIND'],4),('lost-HP',at+F['FLAGS'],seed[at+F['FLAGS']]|128),('stack-reference',L['REFERENCE_DEFINITION_BASE']+row*4,4),('periodic',at+F['INTERVAL']+1,0x3ff00000),('damage-flags',at+F['DAMAGE_FLAGS'],64),('world-absent',L['WORLD_FRAME_INPUT_BASE'],0),('nonfinite-value',at+F['VALUE']+1,0x7ff80000)]
    for label,offset,value in changes:
        w=list(seed);assert w[offset]!=value;w[offset]=value;rows.append(('reject/max-ammo-scaling-'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,t=observe(domain[0]);verify(domain[0],n);n.pop('max_ammo_scaling');return dict(battle=n,skill_trace=t)
def compare(block,domain):return prior.prior.landing.base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/max-ammo-scaling-') and block[0]==64,(name,block[0])
