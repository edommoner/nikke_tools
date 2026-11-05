"""Retain the sealed spatial suite and add consumers of canonical live aim."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('typed_live_aim_parent',ROOT/'research/verify-coordinate-typed-geometry-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from typed_live_aim_cases import fixtures
suite=parent.suite;cross=parent.cross;STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
native_reference=parent.native_reference
SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS

def prepare():
    rows,_=parent.prepare();rows.extend(parent.prepare_spatial(c) for c in fixtures())
    seed=rows[-4][1]
    for name,offset,value in [('source-mode',11,2),('live-literal',4,1),('reserved',12,1)]:
        w=list(seed);w[109968+offset]=value;rows.append(('reject/typed-live-aim/'+name,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def compare(block,domain):
    from unittest.mock import patch
    with patch.object(parent,'native_reference',native_reference):return parent.compare(block,domain)

def validate_rejection(block,name):
    assert name.startswith(('reject/typed-geometry/','reject/typed-live-aim/')) and block[0]==64,(name,block[0])
