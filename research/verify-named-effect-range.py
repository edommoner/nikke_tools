"""Shared event state feeds deterministic named radial selection on both APIs."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_effect_range_specs import *
from portable_effect_range_cases import fixtures,native
import engine_worker
from test_target_counter_runtime import NAMES
s=importlib.util.spec_from_file_location('range_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=INPUT,OUTPUT=OUTPUT,SOURCE=SOURCE);STRICT_WIRE_DIMENSIONS=True

def prepare():
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES];entries=[]
    for case in fixtures():
        w,m=compile_program(chars,list(zip(case['effects'],[NAMES[i] for i in case['owners']])),case['script'],[1000]*5,case['selection'],model=MODEL)
        entries.append((case['name'],w,(case,m)))
    seed=entries[0][1]
    for name,offset,value in [('magic',BASE,0),('version',BASE+1,2),('who',BASE+2,5),('target-count',BASE+4,9),('reserved',BASE+7,1),('unused-target',BASE+32+5*16,1),('unknown-definition',BASE+23,0x80000000),('nan-radius',BASE+11,0x7ff80000),('negative-shape',BASE+32+7,0xbff00000)]:
        w=list(seed);w[offset]=value;entries.append(('reject/named-range/'+name,w,None))
    data=array.array('I',[len(entries)])
    for _,w,_ in entries:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return entries,data.tobytes()

def native_reference(domain):return native(domain[0])
def compare(words,domain):
    if words[0]!=0:raise AssertionError('Named radial selection status '+str(words[0]))
    observed=decode(words,domain[1]);expected=native_reference(domain)
    if observed!=expected:raise AssertionError((domain[0]['name'],observed,expected))
    return expected
