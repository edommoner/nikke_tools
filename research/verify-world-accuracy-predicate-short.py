"""Shared accuracy predicates against the existing full-battle oracle."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('manual_swap_gpu_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_accuracy_predicate_cases import fixtures
from portable_accuracy_predicate_contracts import verify
from world_accuracy_predicate_native import observe
from portable_specs import LIMITS as L

def prepare():
    entries=[]
    for case in fixtures():
        words,meta,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,meta,bindings)))
    assert len(entries)==26
    seed=entries[1][1];at=L['CONDITION_BASE']+2*L['CONDITION_WORDS']
    for label,changes in [('stat-minus-one',[(at+1,0xffffffff)]),('stat-outside',[(at+1,64)]),('stat-unported',[(at+1,1)]),('nan',[(at+2,0),(at+3,0x7ff80000)]),('positive-infinity',[(at+2,0),(at+3,0x7ff00000)]),('negative-infinity',[(at+2,0),(at+3,0xfff00000)])]:
        words=list(seed)
        for index,value in changes:words[index]=value
        entries.append(('reject/accuracy-predicate-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native);native.pop('accuracy_predicate')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/accuracy-predicate-') and block[0]==64
