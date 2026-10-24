"""Whole-buffer native hypot proof for the common integer-only geometry norm."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_coordinate_math_cases import vectors,native_bits,compatible_bits
spec=importlib.util.spec_from_file_location('coordinate_math_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
SOURCE='gpu/coordinate_math_probe.slang';INPUT_WORDS=8;OUTPUT_WORDS=8;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=8,OUTPUT=8,inspect_native=lambda case:native_reference(case))
def native_reference(domain):
    a,b=domain;value=native_bits(a,b);assert value==compatible_bits(a,b),(hex(a),hex(b),'native versus exact rounding');return dict(bits=value)
def prepare():
    entries=[]
    for i,(a,b) in enumerate(vectors()):entries.append(('coordinate-hypot/'+str(i),[0x43484e31,1,a&0xffffffff,a>>32,b&0xffffffff,b>>32,0,0],(a,b)))
    for label,at,value in [('magic',0,0),('reserved',7,1)]:
        words=list(entries[0][1]);words[at]=value;entries.append(('reject/coordinate-hypot-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,w,_ in entries:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def compare(block,domain):
    expected=native_reference(domain);v=expected['bits'];assert list(block)==[0,0x43484e31,v&0xffffffff,v>>32,0,0,0,0],(domain,'hypot rounded bits or unused words');return expected
def validate_rejection(block,name):assert name.startswith('reject/coordinate-hypot-') and list(block)==[64,0,0,0,0,0,0,0]
