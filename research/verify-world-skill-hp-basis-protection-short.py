"""Only the four new repairs; use the same HP/full-battle comparators."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hp_protection_base',ROOT/'research/verify-world-skill-hp-basis-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_skill_hp_basis_protection_cases import fixtures
native_reference,compare=base.native_reference,base.compare
def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
