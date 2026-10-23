"""Original full Asuka WILLE input and complete projectile/native decoder."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('named_removal_roster_gpu',ROOT/'research/verify-world-projectile-rosters.py');roster=importlib.util.module_from_spec(s);s.loader.exec_module(roster)
s=importlib.util.spec_from_file_location('named_removal_roster_base',ROOT/'research/verify-world-named-enemy-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_named_enemy_removal_roster_cases import fixtures
from portable_named_enemy_removal_roster_contracts import verify
from world_named_enemy_removal_roster_native import observe

def prepare():
    rows=[]
    for c in fixtures():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=roster.compile_projectile_battle(p);assert len(m['effects'])==80;rows.append((c['name'],w,(c,m,p,w)))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,_=observe(domain[0]);verify(domain[0],n);n.pop('named_enemy_removal');return n
def compare(block,domain):
    c,m,p,w=domain;expected=native_reference(domain);_,_,_,diff=roster.compare(block,p,(w,m),expected['battle'],expected['projectile_shots']);assert block[0]==0 and not diff,(c['name'],block[0],diff[:8]);return expected
def validate_rejection(block,name):raise AssertionError('No roster rejection inputs')
