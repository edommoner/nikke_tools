"""Both sampled pending queues share native observation and the complete wire."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('sampled_burst_parent',ROOT/'research/verify-coordinate-sampled-skill-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_sampled_burst_cases import fixtures
from world_coordinate_sampled_burst_native import observe
from world_coordinate_aim_native import capture
from portable_coordinate_sampled_burst_wire import SOURCE,INPUT_WORDS,OUTPUT_WORDS,BASE,WORDS,ENTRIES,HITS,HEAD,check_schema
from portable_coordinate_sampling_bank import LAYOUT as BANK
STRICT_WIRE_DIMENSIONS=True;suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);cross=parent.cross;compile_case=parent.compile_case

def prepare():
    check_schema(ROOT);rows,_=parent.prepare()
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    from portable_specs import LIMITS as L
    c=next(c for c in fixtures() if c['name'].endswith('/optin-all-parts'));w,m,_,_=compile_case(c);source=next(i for i,e in enumerate(c['effects']) if e.get('land_in_full_burst'));row=m['binding_source_indices'].index(source)
    for label,at,value in [('descriptor',L['MODE_BASE']+row*L['MODE_WORDS']+17,0),('pending-kind',L['DAMAGE_DEFINITION_BASE']+row*8+6,3),('stage',L['WEAPON_BASE']+3,(w[L['WEAPON_BASE']+3]&~7)|2)]:
        bad=list(w);bad[at]=value;rows.append(('reject/sampled-burst/'+label,bad,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    if not domain[0].get('sampled_burst'):return parent.native_reference(domain)
    with capture(domain[0]) as aim:n,t=observe(domain[0])
    n['coordinate_aim']=aim;return n

def compare(block,domain):
    if not domain[0].get('sampled_burst'):
        assert not any(block[BASE:BASE+WORDS]),'No pending amounts in inherited nonpending worlds'
        return parent.compare(block[:BASE],domain)
    from world_coordinate_sampled_skill_native import creation_indices,trace_view
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.parent.compare_observed(block[:BASE],domain,n,check_parent=False,trace_view=trace_view(n['skill_trace'],indices),sampled_burst_totals=True)
    expected=[0]*WORDS;h=HEAD
    batches=n['sampled_burst_batches'];last=batches[-1] if batches else dict(time=0,entries=[])
    assert block[h]==len(last['entries']),'Combined pending birth count'
    timed=[b['time'] for b in batches if b['entries']];saved_time=timed[-1] if timed else 0.
    assert list(block[h+1:h+3])==list(struct.unpack('<II',struct.pack('<d',saved_time)))
    calls=[r for r in n['sampled_legacy_damage'] if r['time']==last['time']]
    assert block[h+3]==len(calls),'All legacy critical calculations captured before landing'
    for row in calls:
        at=(row['index']*HITS+row['hit']-1)*2
        assert 0<=row['index']<ENTRIES and 1<=row['hit']<=HITS
        expected[at:at+2]=struct.unpack('<II',struct.pack('<d',float(row['damage'])))
    assert list(block[BASE:BASE+WORDS])==expected,'Exact amount for each pending entry/hit; unused slots zero'
    return n

def validate_rejection(block,name):
    if name.startswith('reject/sampled-burst/'):assert block[0]==64
    else:parent.validate_rejection(block[:BASE],name)
