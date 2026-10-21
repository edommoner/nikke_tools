"""Cumulative priority suite: retained projectile contracts plus new operators."""
import array
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('readiness_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross,compare=base.suite,base.cross,base.compare

def prepare():
    entries,_=base.prepare();entries+=base.development_entries()
    from portable_burst_recipient_cases import negative_inputs
    entries+=negative_inputs(suite.compile_case)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
