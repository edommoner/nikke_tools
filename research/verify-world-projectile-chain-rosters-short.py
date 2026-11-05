"""Original profiles through the same shared CUDA/Metal runtime."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('projectile_chain_real_prior',ROOT/'research/verify-world-max-ammo-scaling-rosters-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
roster,suite,cross=prior.roster,prior.suite,prior.cross
from portable_projectile_chain_roster_cases import fixtures
from world_projectile_chain_native import observe
from portable_projectile_chain_contracts import verify

def prepare():
    rows=[]
    for c in fixtures():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=roster.compile_projectile_battle(p);assert len(m['effects'])==len(p['effects']);rows.append((c['name'],w,(c,m,p,w)))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,_=observe(domain[0]);verify(domain[0],n);return n
def compare(block,domain):
    c,m,p,w=domain;expected=native_reference(domain)
    _,_,_,diff=roster.compare(block,p,(w,m),expected['battle'],expected['projectile_shots']);assert block[0]==0 and not diff,(c['name'],block[0],diff[:8])
    return expected
def validate_rejection(block,name):raise AssertionError('No original roster rejection inputs')
