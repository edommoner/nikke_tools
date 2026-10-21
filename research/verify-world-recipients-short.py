"""Focused host admission extension; all execution stays in the shared entry."""
import array
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('recipient_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross,compare=base.suite,base.cross,base.compare

def prepare():
    from portable_recipient_extension_cases import fixtures
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
