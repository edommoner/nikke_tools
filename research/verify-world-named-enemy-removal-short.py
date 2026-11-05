"""Both removal scopes, native full battle and preserved mutation evidence."""
import array,importlib.util,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('named_removal_base',Path(__file__).with_name('verify-world-named-enemy-short.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_named_enemy_removal_cases import fixtures
from portable_named_enemy_removal_contracts import verify
from world_named_enemy_removal_native import observe
from portable_specs import LIMITS as L,FIELDS as F
from portable_named_enemy_specs import MAGIC,OFFSET

def prepare():
    rows=[]
    for c in fixtures():
        w,m,p=suite.compile_case(c);rows.append((c['name'],w,(c,m,p)))
    seed=rows[3][1];row=len(rows[3][2][0]['effects'])-1;at=L['MODE_BASE']+row*L['MODE_WORDS']+OFFSET
    raw=[('global-target-smuggle',L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['TARGET'],0),('name-overflow',at+1,257),('count',L['DAMAGE_DEFINITION_BASE']+row*L['DAMAGE_DEFINITION_WORDS']+1,127),('no-combat',3,0),('no-world',L['WORLD_FRAME_INPUT_BASE'],0),('no-state',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0)]
    for label,pos,value in raw:
        w=list(seed);assert w[pos]!=value;w[pos]=value;rows.append(('reject/named-enemy-removal-'+label,w,None))
    w=list(rows[7][1]);r=len(rows[7][2][0]['effects'])-1;pos=L['MODE_BASE']+r*L['MODE_WORDS']+OFFSET;w[pos:pos+4]=[MAGIC,1,0,0];rows.append(('reject/named-enemy-removal-global-descriptor',w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    c=domain[0];n,t=observe(c);verify(c,n);n.pop('named_enemy_removal');return dict(battle=n,skill_trace=t)
def compare(block,domain):return base.base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/named-enemy-removal-') and block[0]==64
