"""Same native world comparator plus bounded cache lifecycle assertions."""
import array
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lazy_bank_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross


def prepare():
    from portable_lazy_bank_cases import fixtures,negative_inputs
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    entries+=negative_inputs(suite.compile_case)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def compare(block,domain):
    native=base.compare(block,domain);case=domain[0]
    if 'expected_cache_groups' in case and block[10]!=case['expected_cache_groups']:
        raise ValueError('Unexpected lazy cache sharing')
    if case.get('expect_cache_saturation') and (block[10]!=1024 or block[12]==0):
        raise ValueError('Fixture did not exercise bounded cache reuse')
    return native


def validate_rejection(block,name):
    if name=='reject/lazy-bank-error-after-warm' and (block[8]<120 or block[10]!=1024 or block[12]==0):
        raise ValueError('Expected execution rejection after bounded cache reuse, not an admission rejection')
