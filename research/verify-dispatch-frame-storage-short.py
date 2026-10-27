"""Exact bit-pattern/state-isolation proof, not a native battle certificate."""
import sys,importlib.util
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_dispatch_frames import FIELDS,encode,decode,check_frame_type
s=importlib.util.spec_from_file_location('frame_probe_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=40,OUTPUT=1040)
SOURCE='gpu/dispatch_frame_storage_probe.slang'
STRICT_WIRE_DIMENSIONS=True

def cases():
    edge={name:(-(1<<31) if typ=='int' else (1<<64)-1 if typ=='uint64_t' else 0xffffffff) for name,_,typ,_ in FIELDS}
    edge.update(value=0x7ff8000000000001,time=0x8000000000000000,healthValue=1,healthPrevious=0x0010000000000001)
    return [(0,{}),(1,edge),(2,edge),(3,edge),(4,{})]

def prepare():
    check_frame_type(ROOT)
    rows=[]
    for index,(op,values) in enumerate(cases()):
        words=[op,0,0,0,0,0,0,0]+encode(values)
        rows.append((f'dispatch-frame-storage/{op}',words,dict(index=index,op=op,values=values)))
    return rows,None

def native_reference(domain):
    header=[0,0x46524d31,int(domain['op'] in (3,4)),32,32,domain['index'],0x12345678]+[0]*9
    frames=[]
    for slot in range(32):
        values=decode(encode(domain['values']));values['cursor']=(values['cursor']+slot)&0xffffffff
        if slot==31 and domain['op']==1:values['cursor']=(values['cursor']+1)&0xffffffff;values['value']^=1<<63
        if slot==31 and domain['op']==2:values['cursor']=(values['cursor']+3)&0xffffffff;values['value']^=0x80000001<<32
        frames.extend(encode(values))
    return header+frames

def compare(block,domain):
    expected=native_reference(domain)
    assert len(block)==1040 and list(block)==expected,'Full frame storage words differ'
    return expected

def validate_rejection(block,name):raise AssertionError('No skipped/rejection-only frame probe cases')
