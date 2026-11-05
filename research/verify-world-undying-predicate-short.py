"""Shared undying predicates against the existing full-battle oracle."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('manual_swap_gpu_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_undying_predicate_cases import fixtures
from portable_undying_predicate_contracts import verify
from world_undying_predicate_native import observe
from portable_specs import LIMITS as L

def prepare():
    entries=[]
    for case in fixtures():
        words,meta,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,meta,bindings)))
    assert len(entries)==22
    seed=entries[1][1];at=L['CONDITION_BASE']+2*L['CONDITION_WORDS']
    for label,changes in [('name',[(at+1,1)]),('argument',[(at+2,0),(at+3,0x3ff00000)]),('nan',[(at+2,0),(at+3,0x7ff80000)]),('infinity',[(at+2,0),(at+3,0x7ff00000)]),('non-combat',[(3,0)]),('passive',[(L['EVENT_BASE']+2*L['EVENT_WORDS'],0),(L['EVENT_BASE']+2*L['EVENT_WORDS']+6,1)])]:
        words=list(seed)
        for index,value in changes:words[index]=value
        if label=='passive':
            from portable_trigger_specs import pack_event_candidates
            pack_event_candidates(words,L)
        entries.append(('reject/undying-predicate-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native);native.pop('undying_predicate')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/undying-predicate-') and block[0]==64
