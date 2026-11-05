"""Shared CUDA/Metal ally-burst cases using the unchanged full battle comparator."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('ally_burst_base',ROOT/'research/verify-world-projectile-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_ally_burst_cases import fixtures
from world_ally_burst_native import observe
from portable_ally_burst_contracts import verify

def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    words=list(entries[1][1]);words[3]=0;entries.append(('reject/ally-burst-no-combat',words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):
    case,_,_=domain;native,trace=observe(case);verify(case,native);native.pop('ally_burst_events')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):
    case,metadata,bindings=domain;expected=native_reference(domain)
    actual=suite.decoded(block,metadata,case,bindings)
    changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]]
    assert block[0]==0 and not changed,(case['name'],block[0],changed)
    assert suite.reload.charge.team.skill_trace(block,metadata)==expected['skill_trace'],(case['name'],'skill trace')
    return expected
def validate_rejection(block,name):
    assert name=='reject/ally-burst-no-combat' and block[0]==64
