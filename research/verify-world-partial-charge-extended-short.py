"""All dynamic partial/full native contracts through the shared comparator."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('partial_extended_base',ROOT/'research/verify-world-partial-charge-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross,native_reference,compare=base.suite,base.cross,base.native_reference,base.compare
from portable_partial_charge_extended_cases import fixtures


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def validate_rejection(block,name):raise AssertionError('No raw rejections in partial-charge extended contracts')
