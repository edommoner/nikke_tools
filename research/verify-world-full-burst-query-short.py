"""Deferred HP basis and zero-hit query-only battles using the existing full decoder."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('query_landing_base',ROOT/'research/verify-world-full-burst-landing-short.py');landing=importlib.util.module_from_spec(s);s.loader.exec_module(landing)
suite,cross=landing.suite,landing.cross
from portable_full_burst_query_cases import fixtures
from portable_full_burst_query_contracts import verify
from world_full_burst_query_native import observe

def prepare():
    rows=[]
    for c in fixtures():
        c=landing.wire_case(c);w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    c=domain[0];n,t=observe(c);verify(c,n,t);q=n.pop('full_burst_query');n.pop('full_burst_landing');return dict(battle=n,skill_trace=t,full_burst_query=q)
def compare(block,domain):return landing.base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):raise AssertionError('No query rejection cases')
