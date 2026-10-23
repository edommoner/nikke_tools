"""Full-profile code/weapon leftmost battles on the shared GPU entry."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('leftmost_rosters_base',ROOT/'research/verify-world-projectile-rosters.py');roster=importlib.util.module_from_spec(s);s.loader.exec_module(roster)
s=importlib.util.spec_from_file_location('leftmost_rosters_suite',ROOT/'research/verify-world-leftmost-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_leftmost_roster_cases import fixtures
from world_leftmost_roster_native import observe
from portable_leftmost_roster_contracts import verify

def prepare():
    entries=[]
    for c in fixtures():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=roster.compile_projectile_battle(p);entries.append((c['name'],w,(c,m,p,w)))
    data=array.array('I',[len(entries)])
    for _,w,_ in entries:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return entries,data.tobytes()

def native_reference(domain):
    n,_=observe(domain[0]);verify(domain[0],n);n.pop('leftmost_selections');return n

def compare(block,domain):
    c,m,p,w=domain;expected=native_reference(domain)
    _,_,_,diff=roster.compare(block,p,(w,m),expected['battle'],expected['projectile_shots'])
    assert block[0]==0 and not diff,(c['name'],block[0],diff[:8])
    return expected
