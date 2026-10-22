"""Shared manual mode reloads against the existing full-battle oracle."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('manual_swap_gpu_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_manual_swap_cases import fixtures
from portable_manual_swap_contracts import verify
from world_manual_swap_native import observe
from portable_specs import LIMITS as L

def prepare():
    entries=[]
    for case in fixtures():
        if case['name']=='manual-swap-cover-pump-order':
            try:suite.compile_case(case)
            except ValueError as error:assert 'Non-hold sequence' in str(error)
            else:raise AssertionError('Cover must remain rejected until its physical adapter exists')
            continue
        words,meta,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,meta,bindings)))
    assert len(entries)==23
    seed=entries[0][1];at=L['WORLD_RELOAD_INPUT_BASE']
    for label,changes in [('mask-overflow',[(at+3,32)]),('missing-tag',[(at+4,0)]),('wrong-tag',[(at+4,1)]),('orphan-tag',[(at+3,0)]),('reserved5',[(at+5,1)]),('reserved6',[(at+6,1)]),('reserved7',[(at+7,1)])]:
        words=list(seed)
        for index,value in changes:words[index]=value
        entries.append(('reject/manual-swap-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native);native.pop('manual_swap')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/manual-swap-') and block[0]==64
