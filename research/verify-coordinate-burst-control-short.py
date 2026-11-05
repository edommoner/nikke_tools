"""Burst policy uses GPU clocks in the same shared battle/weapon executor."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('burst_control_parent',ROOT/'research/verify-coordinate-squad-mode-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_burst_control_specs import SOURCE,INPUT_BASE,STATE_BASE,MAGIC,WORDS,empty
from portable_coordinate_burst_control_cases import fixtures
from world_frame_native import roster_names
from world_burst_control_native import resolve
import world_coordinate_comparison_context as NATIVE_COMPARISON_CONTEXT
INPUT_WORDS=INPUT_BASE+WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True;suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);cross=parent.cross

def compile_case(case):
    if not case.get('burst_controls'):
        w,m,b,d=parent.compile_case(case);return w+empty(),m,b,d
    cfg,extra=resolve(case,roster_names(case));lower=copy.deepcopy(case)
    for control in lower['controls']:control.pop('burst',None)
    w,m,b,d=parent.compile_case(lower);return w+extra,m,b,d

def prepare():
    old,_=parent.prepare();rows=[(name,w+empty(),d) for name,w,d in old]
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    seed=next(w for name,w,_ in rows if name=='coordinate-burst-control/delay-first')
    for label,offset,value in [('magic',0,0),('version',1,2),('disable-nonempty',2,0),('cycle-capacity',3,17),('reserved',7,1),('nan-delay',9,0x7ff80000),('wait-low',11,0x3fd00000),('pattern-kind',12,3),('unused-sequence',128,1)]:
        w=list(seed);w[INPUT_BASE+offset]=value;rows.append(('reject/burst-control/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):return parent.native_reference(domain)

def native_comparison_adapter(domain):
    return NATIVE_COMPARISON_CONTEXT.choose(parent.parent.parent.parent,domain)

def compare(block,domain):
    if not domain[0].get('burst_controls'):return parent.compare(block,domain)
    h=STATE_BASE;clean=list(block);clean[h:h+18]=[0]*18
    # The existing squad comparator recompiles static cover-policy mask only.
    # Keep original controls for native execution, strip the independently owned
    # burst axis only for this legacy static packer. No canonical state changes.
    original=parent.parent.compile_case
    def mask_case(case):
        lower=copy.deepcopy(case)
        for control in lower['controls']:control.pop('burst',None)
        return original(lower)
    with patch.object(parent.parent,'compile_case',mask_case):n=parent.compare(clean,domain)
    return compare_state(block,n)
def compare_state(block,n):
    h=STATE_BASE
    ticks=n['burst_controls']['ticks'];last=ticks[-1]
    assert block[h]==MAGIC and block[h+1]==last['cycles']
    assert list(block[h+2:h+4])==list(struct.unpack('<II',struct.pack('<d',last['stage_open'])))
    assert list(block[h+4:h+9])==last['stages'] and block[h+9]==0
    a=0xcbf29ce484222325;b=0x84222325cbf29ce4;mask=(1<<64)-1
    for tick in ticks:
        for word in tick['words']:
            a=((a^word)*0x100000001b3)&mask;b=(((b<<7)|(b>>57))^word*0x9e3779b185ebca87)&mask
    assert list(block[h+10:h+14])==[a&0xffffffff,a>>32,b&0xffffffff,b>>32],'Every post-tick burst state'
    assert block[h+14]==len(ticks) and not any(block[h+15:h+18])
    return n

def validate_rejection(block,name):
    if name.startswith('reject/burst-control/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
