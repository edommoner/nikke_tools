"""Storage-object observations plus the unchanged world battle comparator."""
import array
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('storage_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
cross=base.cross
suite=SimpleNamespace(INPUT=base.suite.INPUT,OUTPUT=base.suite.OUTPUT,
                      compile_case=base.suite.compile_case,inspect_native=base.suite.inspect_native)


def prepare():
    from portable_healing_storage_cases import fixtures,negative_inputs
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    entries+=negative_inputs(suite.compile_case)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def decoded_storage(block,metadata,case):
    from portable_runtime import decode
    from portable_specs import LIMITS as L
    actual=decode(block[:159744],metadata);rows=[]
    for carrier in actual['carriers']:
        row=carrier['definition']
        if not carrier['active'] or case['effects'][row].get('stat')!='heal_overcharge_store':continue
        storage=carrier.get('protection',{});current=storage.get('current',{});capacity=storage.get('capacity',{})
        rows.append(dict(row=row,owner=case['owners'][row],activated=carrier['activated'],end=carrier['end'],
                         initialized=bool(storage),recipients=sorted(int(w) for w in capacity),
                         current=[current.get(str(w),0.0) for w in range(5)],
                         capacity=[capacity.get(str(w),0.0) for w in range(5)]))
    return sorted(rows,key=lambda r:(r['row'],r['recipients']))


def compare(block,domain):
    case,metadata,bindings=domain
    native,trace=suite.inspect_native(case)
    actual=base.suite.decoded(block,metadata,case,bindings)
    actual['healing_storage']=decoded_storage(block,metadata,case)
    changed=[k for k in native if k!='scope' and actual[k]!=native[k]]
    if block[0]!=0 or changed:raise ValueError(str(dict(status=block[0],changed=changed,storage=actual['healing_storage'],expected_storage=native['healing_storage'])))
    if base.suite.reload.charge.team.skill_trace(block,metadata)!=trace:raise ValueError('Storage skill trace differs')
    return dict(battle=native,skill_trace=trace)
