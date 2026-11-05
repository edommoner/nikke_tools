"""Live queue512, overflow513 and final deferred ownership through shared decoders."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('capacity_queue_base',ROOT/'research/verify-world-full-burst-queue-short.py');queue=importlib.util.module_from_spec(s);s.loader.exec_module(queue)
suite,cross=queue.suite,queue.cross
from portable_specs import LIMITS as L
from portable_full_burst_capacity_cases import fixtures
from portable_full_burst_capacity_contracts import verify
from world_full_burst_capacity_native import observe

def prepare():
    rows=[]
    for c in fixtures():
        c=queue.landing.wire_case(c);w,m,b=suite.compile_case(c)
        rows.append((('reject/' if c['contract']['reject'] else '')+c['name'],w,None if c['contract']['reject'] else (c,m,b)))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    c=domain[0];n,t=observe(c);verify(c,n,t);pending=n.pop('full_burst_capacity')['entries'];n.pop('full_burst_queue')
    for key in ('parts_skill_events','parts_skill_lifecycle','parts_skill_accounting'):n.pop(key,None)
    summary=c['combat'].get('trace')=='summary'
    return dict(battle=n,skill_trace=[] if summary else t,final_deferred=pending,summary_packet_count=len(t) if summary else None)
def final_deferred(block,domain):
    at=L['PENDING_STATE_BASE'];legacy,count=block[at],block[at+3]
    assert legacy+count<=512
    rows=[]
    for i in range(count):
        pos=at+4+(legacy+i)*8;row=block[pos]
        assert row<len(domain[0]['effects'])
        assert domain[0]['effects'][row].get('land_in_full_burst') is True
        rows.append(dict(owner=domain[0]['owners'][row],name=domain[0]['effects'][row]['name'],hits=block[pos+5]))
    return rows
def compare(block,domain):
    expected=native_reference(domain)
    assert final_deferred(block,domain)==expected['final_deferred'],(domain[0]['name'],'final deferred queue')
    if expected['summary_packet_count'] is not None:assert block[6]==expected['summary_packet_count'],(domain[0]['name'],'summary packet total',block[6],expected['summary_packet_count'])
    return queue.base.compare_expected(block,domain,expected)
def validate_rejection(block,name):
    assert name=='reject/full-burst-capacity-live-513-reject' and block[0]==64,(name,block[0])
