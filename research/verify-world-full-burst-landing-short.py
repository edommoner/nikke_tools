"""Cast-latched full-burst landings with the existing full-battle decoder."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('full_burst_gpu_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_full_burst_landing_cases import fixtures
from portable_full_burst_landing_contracts import verify
from world_full_burst_landing_native import observe
from portable_specs import LIMITS as L,FIELDS as F

def wire_case(c):
    c=copy.deepcopy(c);c.update(post_fire_delays=[0]*5,controls=[{} for _ in range(5)],control_mode='solo');return c

def prepare():
    rows=[]
    for c in fixtures():
        c=wire_case(c);w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    seed=rows[0][1];row=next(i for i,e in enumerate(rows[0][2][0]['effects']) if e.get('name')=='landing');at=L['DAMAGE_DEFINITION_BASE']+row*L['DAMAGE_DEFINITION_WORDS']
    raw=[('mode',at+6,3),('count-overflow',at+7,257),('negative-overflow',at+7,(-257)&0xffffffff),('reference-without-descriptor',at+7,4096),('reference-overflow',at+7,4352),('missing-mode',at+6,0),('count-disagreement',at+2,2),('no-combat',3,0),('wrong-stage',L['WEAPON_BASE']+3,2),('no-cast',L['EVENT_BASE']+row*L['EVENT_WORDS'],0),('missing-tag',L['MODE_BASE']+row*L['MODE_WORDS']+17,0),('bad-tag',L['MODE_BASE']+row*L['MODE_WORDS']+17,1),('reserved',L['MODE_BASE']+row*L['MODE_WORDS']+18,1)]
    for name,pos,value in raw:
        w=list(seed);assert w[pos]!=value;w[pos]=value;rows.append(('reject/full-burst-landing-'+name,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    c=domain[0];n,t=observe(c);verify(c,n);n.pop('full_burst_landing');return dict(battle=n,skill_trace=t)
def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/full-burst-landing-') and block[0]==64
