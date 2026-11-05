"""Shared CUDA/Metal lifetime cases and original native execution."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('healing_lifetime_base',ROOT/'research/verify-world-heal-charge-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
suite,cross=prior.suite,prior.cross
from portable_heal_charge_lifetime_cases import fixtures
from portable_heal_charge_lifetime_contracts import verify
from world_heal_charge_lifetime_native import observe
from portable_heal_charge_observation import compare_final

def prepare():
    rows=[]
    for c in fixtures():
        w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    n,t=observe(domain[0]);verify(domain[0],n);return dict(battle=n,skill_trace=t)
def compare(block,domain):
    expected=native_reference(domain);prior.compare_expected(block,domain,expected)
    compare_final(block,domain[1],domain[0],expected['battle']['healing_charge']);return expected
def validate_rejection(block,name):raise AssertionError('No lifetime rejection inputs')
