"""Sampled skill-mode/group contracts reuse the already sealed GPU source."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
parent=module('sampled_delivery_parent','research/verify-coordinate-sampled-vital-short.py')
groups=module('sampled_delivery_groups','research/verify-coordinate-group-short.py')
from portable_coordinate_sampled_delivery_cases import fixtures
from world_coordinate_sampled_delivery_native import observe
from world_coordinate_aim_native import capture
SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case

def prepare():
    rows,_=parent.prepare()
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    c=next(c for c in fixtures() if c['name'].endswith('/group-body'));w,m,b,d=compile_case(c)
    from portable_specs import LIMITS as L
    events=[L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8 for row in range(w[1]) for slot in range(8) if w[L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8]==62];assert events
    for label,at,value in [('owners',104402,0),('threshold',events[0]+4,129)]:
        bad=list(w);bad[at]=value;rows.append(('reject/sampled-delivery/'+label,bad,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    if not domain[0].get('sampled_delivery'):return parent.native_reference(domain)
    with capture(domain[0]) as aim:n,t=observe(domain[0])
    n['coordinate_aim']=aim;return n

def compare(block,domain):
    if not domain[0].get('sampled_delivery'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.parent.compare_observed(block,domain,n,indices)
    if domain[0].get('sampled_groups'):groups.compare_group_receipts(block[:1507328],domain,n,compare_packets=False)
    return n

def validate_rejection(block,name):
    if name.startswith('reject/sampled-delivery/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
