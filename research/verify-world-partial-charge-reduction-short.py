"""Signed threshold bases through the shared full native comparator."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('partial_reduction_base',ROOT/'research/verify-world-partial-charge-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross,native_reference,compare=base.suite,base.cross,base.native_reference,base.compare
from portable_partial_charge_reduction_cases import fixtures
from portable_specs import LIMITS as L


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[0][1];event=L['EVENT_BASE']+L['EVENT_WORDS']
    for label,changes in [('positive-signed-base',[(event+4,1)]),('wrong-placeholder',[(event+2,0x40000000)]),('unknown-flag',[(event+5,2)]),('never-with-signed-flag',[(event+7,2)])]:
        words=list(seed)
        for at,value in changes:words[at]=value
        assert words!=seed;entries.append(('reject/partial-reduction-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def validate_rejection(block,name):assert name.startswith('reject/partial-reduction-') and block[0]==64
