"""Reuse complete world/native and named-state comparison for named_magnitude."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('named_magnitude_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross,compare=base.suite,base.cross,base.compare


def prepare():
    from portable_named_magnitude_cases import fixtures,negative_inputs
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    entries+=negative_inputs(suite.compile_case)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
