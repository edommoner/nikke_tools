"""Live deferred queue and owned receipt-tail comparison through common decoders."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def load(name):
    s=importlib.util.spec_from_file_location('queue_'+name,ROOT/'research'/('verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
landing=load('full-burst-landing');parts=load('parts-skill');base=landing.base
suite,cross=landing.suite,landing.cross
from portable_full_burst_queue_cases import fixtures
from portable_full_burst_queue_contracts import verify
from world_full_burst_queue_native import observe

def prepare():
    rows=[]
    for c in fixtures():
        c=landing.wire_case(c);w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    c=domain[0];n,t=observe(c);verify(c,n);n.pop('full_burst_queue')
    interrupt=n.get('parts_skill_accounting') if any(p.get('kind')=='interrupt' for p in c.get('patterns',[])) else None
    for key in ('parts_skill_events','parts_skill_lifecycle','parts_skill_accounting'):n.pop(key,None)
    expected=dict(battle=n,skill_trace=t)
    if interrupt is not None:expected['interrupt']=interrupt
    return expected
def compare(block,domain):
    expected=native_reference(domain)
    if 'interrupt' in expected:assert parts.decoded_interrupt(block,domain[2],len(expected['interrupt']['interrupt_damage']))==expected['interrupt']
    return base.compare_expected(block,domain,expected)
def validate_rejection(block,name):raise AssertionError('No queue rejection inputs')
