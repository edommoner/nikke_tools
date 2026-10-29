"""Declared independent cover quantity oracle versus shared CUDA/Metal math."""
import array,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from cover_defense_model import numeric
from portable_cover_defense_numeric_cases import fixtures
spec=importlib.util.spec_from_file_location('cover_numeric_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
SOURCE='gpu/cover_defense_numeric_probe.slang';STRICT_WIRE_DIMENSIONS=True;suite=SimpleNamespace(INPUT=16,OUTPUT=12)
MAGIC=0x43444631

def native_reference(domain):return numeric(*domain[0]['quantities'])

def words(values):
    result=[]
    for value in values:result.extend(struct.unpack('<II',struct.pack('<d',value)))
    return result

def prepare():
    rows=[(c['name'],[MAGIC,1,0,0,*words(c['quantities'])],(c,)) for c in fixtures()]
    for label,at,value in [('magic',0,0),('version',1,2),('flags',2,1),('reserved',3,1),('negative-attack',5,0xbff00000),('negative-coefficient',7,0xbff00000),('negative-cover-base',9,0xbff00000),('nan-percent',11,0x7ff80000),('infinite-received',13,0x7ff00000),('infinite-body',15,0x7ff00000)]:
        w=list(rows[0][1]);w[at]=value;rows.append(('reject/cover-defense-numeric/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def compare(block,domain):
    n=native_reference(domain)
    expected=[0,MAGIC,n['status'],0,*words(n['values'] if n['status']==0 else [0.,0.,0.]),0,0]
    assert list(block)==expected,dict(case=domain[0]['name'],actual=list(block),expected=expected)
    return n

def validate_rejection(block,name):assert name.startswith('reject/cover-defense-numeric/') and list(block)==[64,*([0]*11)]
