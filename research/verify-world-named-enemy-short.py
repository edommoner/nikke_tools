"""Opaque live enemy-state selection through shared full native battle comparison."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('named_enemy_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_named_enemy_cases import fixtures
from portable_named_enemy_contracts import verify
from world_named_enemy_native import observe
from portable_specs import LIMITS as L,FIELDS as F
from portable_named_enemy_specs import MAGIC,OFFSET

def prepare():
    rows=[]
    for c in fixtures():
        w,m,p=suite.compile_case(c);rows.append((c['name'],w,(c,m,p)))
    seed=rows[3][1];row=len(rows[3][2][0]['effects'])-1;at=L['MODE_BASE']+row*L['MODE_WORDS']+OFFSET;d=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
    raw=[('missing-tag',at,0),('bad-tag',at,1),('missing-name',at+1,0),('name-overflow',at+1,257),('flags',at+2,4),('reserved',at+3,1),('no-combat',3,0),('no-world',L['WORLD_FRAME_INPUT_BASE'],0),('no-state',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0)]
    for label,pos,value in raw:
        w=list(seed);assert w[pos]!=value;w[pos]=value;rows.append(('reject/named-enemy-'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    c=domain[0];n,t=observe(c);verify(c,n);n.pop('named_enemy');return dict(battle=n,skill_trace=t)
def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/named-enemy-') and block[0]==64
