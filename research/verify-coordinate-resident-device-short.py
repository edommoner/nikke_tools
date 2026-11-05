"""Four original prefix cases for bounded current-source device validation.

The complete resident source/ABI and whole-tail comparator are unchanged.
This is a scoped first device check, never replacement coverage for all106.
"""
import array,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('resident_device_parent',ROOT/'research/verify-coordinate-resident-arc-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
CASES=('coordinate-typed/control/original-Marciana-3s','coordinate-typed/original-modifier-probe/사쿠라/3s','coordinate-typed/original-modifier-probe/앵커/3s','coordinate-typed/original-modifier-probe/클레이/3s')
BASELINE='research/portable-coordinate-resident-arc-short-expected.json'
suite=parent.suite;SOURCE=parent.SOURCE;STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
cross=parent.cross;native_reference=parent.native_reference;compare=parent.compare;validate_rejection=parent.validate_rejection;native_comparison_adapter=parent.native_comparison_adapter

def prepare():
    rows,_=parent.prepare();baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))['entries']
    if len(rows)!=len(baseline) or tuple(r[0] for r in rows[:4])!=CASES or tuple(r['name'] for r in baseline[:4])!=CASES:
        raise ValueError('Original resident prefix changed; review the explicit device scope')
    selected=rows[:4]
    for (name,words,domain),expected in zip(selected,baseline[:4],strict=True):
        packed=array.array('I',words)
        if sys.byteorder!='little':packed.byteswap()
        if domain is None or len(words)!=suite.INPUT or hashlib.sha256(packed.tobytes()).hexdigest()!=expected['input_sha256']:
            raise ValueError('Complete original device input/native domain changed: '+name)
    return selected,None
