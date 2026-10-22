"""Natural full-profile accuracy predicate with complete original definitions."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('manual_swap_real_base',ROOT/'research/verify-world-roster-regression-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_accuracy_predicate_roster_cases import fixtures

def prepare():
    entries=[]
    for case in fixtures():
        prepared=base.real.engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,metadata=base.real.compile_projectile_battle(prepared)
        entries.append((case['name'],words,(case,prepared,words,metadata)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
compare=base.compare
