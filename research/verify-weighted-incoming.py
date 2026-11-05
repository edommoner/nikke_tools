"""Strict full-word shared allocation comparison; no battle-support claim."""
import array,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from incoming_weighted_allocation import allocate
from portable_weighted_incoming_cases import fixtures
spec=importlib.util.spec_from_file_location('weighted_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
SOURCE='gpu/incoming_weighted_probe.slang';STRICT_WIRE_DIMENSIONS=True;suite=SimpleNamespace(INPUT=16,OUTPUT=20)
MAGIC=0x57414c31
def words(values):
    out=[]
    for value in values:out.extend(struct.unpack('<II',struct.pack('<d',value)))
    return out
def native_reference(domain):return allocate(*domain[0]['args'])
def prepare():
    rows=[]
    for c in fixtures():
        amount,mask,caster,self_weight,other_weight,cover_weight,cover=c['args']
        rows.append((c['name'],[MAGIC,1,mask,caster,*words([amount,self_weight,other_weight,cover_weight]),int(cover),0,0,0],(c,)))
    for label,at,value in [('magic',0,0),('version',1,2),('empty',2,0),('mask',2,32),('caster',3,5),('negative-amount',5,0xbff00000),('nan-amount',5,0x7ff80000),('zero-weight',7,0),('negative-weight',9,0xbff00000),('infinite-weight',11,0x7ff00000),('cover-flag',12,2),('dead-cover-owner',12,1),('reserved',15,1)]:
        w=list(rows[0][1]);w[at]=value
        if label=='zero-weight':w[6]=0
        if label=='dead-cover-owner':w[3]=1
        rows.append(('reject/weighted-incoming/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def compare(block,domain):
    n=native_reference(domain)
    expected=[0,MAGIC,n['status'],n['active_mask'],*words([n['total'],*n['shares']] if n['status']==0 else [0.]*7),0,0]
    assert list(block)==expected,dict(case=domain[0]['name'],actual=list(block),expected=expected)
    return n
def validate_rejection(block,name):assert name.startswith('reject/weighted-incoming/') and list(block)==[64,*([0]*19)]
