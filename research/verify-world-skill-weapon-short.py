"""Scoped native-equivalent metadata: eight witnesses and two original battles."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def load(tag,file):
    s=importlib.util.spec_from_file_location(tag,ROOT/'research'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=load('skill_weapon_base','verify-world-leftmost-short.py');roster=load('skill_weapon_roster','verify-world-projectile-rosters.py')
suite,cross=base.suite,base.cross
from portable_skill_weapon_cases import fixtures as synthetic
from portable_skill_weapon_roster_cases import fixtures as real
from world_skill_weapon_native import observe
from world_skill_weapon_roster_native import observe as observe_real
from portable_skill_weapon_contracts import verify
from portable_skill_weapon_roster_contracts import verify as verify_real

def prepare():
    rows=[]
    for c in synthetic():
        if c['contract']['reference_model_gap']:continue
        w,m,p=suite.compile_case(c);rows.append((c['name'],w,(c,m,p,w)))
    for c in real():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=roster.compile_projectile_battle(p);rows.append((c['name'],w,(c,m,p,w)))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    c=domain[0]
    if 'body' in c:n,t=observe_real(c);verify_real(c,n);n.pop('skill_weapon_calls');return n
    n,t=observe(c);verify(c,n);n.pop('skill_weapon_calls');return dict(battle=n,skill_trace=t)

def compare(block,domain):
    c,m,p,w=domain;expected=native_reference(domain)
    if 'body' in c:
        _,_,_,diff=roster.compare(block,p,(w,m),expected['battle'],expected['projectile_shots']);assert block[0]==0 and not diff,(c['name'],block[0],diff[:8])
    else:
        actual=suite.decoded(block,m,c,p)
        if c.get('observe_healing_storage'):actual['healing_storage']=base.base.base.storage.decoded_storage(block,m,c)
        changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]]
        assert block[0]==0 and not changed,(c['name'],block[0],changed)
        assert suite.reload.charge.team.skill_trace(block,m)==expected['skill_trace'],(c['name'],'full skill trace')
    return expected
