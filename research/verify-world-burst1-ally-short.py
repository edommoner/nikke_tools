"""B1-presence native battles plus typed raw rejection cases, both GPUs."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('burst1_base',ROOT/'research/verify-world-skill-weapon-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_burst1_ally_cases import fixtures
from world_burst1_ally_native import observe
from portable_burst1_ally_contracts import verify
from portable_specs import LIMITS as L

def prepare():
    rows=[]
    for c in fixtures():
        w,m,p=suite.compile_case(c);rows.append((c['name'],w,(c,m,p,w)))
    for index in (0,6):
        seed=rows[index][1];at=L['CONDITION_BASE']+L['CONDITION_WORDS'];assert seed[at] in (31,32)
        for label,offset,value in [('name',1,1),('arg',3,0x3ff00000),('nan',3,0x7ff80000)]:
            w=list(seed);w[at+offset]=value;rows.append(('reject/burst1-'+str(seed[at])+'-'+label,w,None))
    for label,at in [('no-combat',3),('no-world',L['WORLD_FRAME_INPUT_BASE'])]:
        w=list(rows[0][1]);w[at]=0;rows.append(('reject/burst1-'+label,w,None))
    data=array.array('I',[len(rows)])
    for _,w,_ in rows:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()

def native_reference(domain):
    n,t=observe(domain[0]);verify(domain[0],n);n.pop('burst1_ally_conditions');return dict(battle=n,skill_trace=t)
def compare(block,domain):
    c,m,p,w=domain;expected=native_reference(domain);actual=suite.decoded(block,m,c,p)
    if c.get('observe_healing_storage'):actual['healing_storage']=base.base.base.base.storage.decoded_storage(block,m,c)
    changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]]
    assert block[0]==0 and not changed,(c['name'],block[0],changed)
    assert suite.reload.charge.team.skill_trace(block,m)==expected['skill_trace'],(c['name'],'full skill trace')
    return expected
def validate_rejection(block,name):assert name.startswith('reject/burst1-') and block[0]==64
