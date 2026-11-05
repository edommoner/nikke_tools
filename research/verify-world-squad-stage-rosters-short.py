"""Reuse the original full-profile comparator with all Red Hood definitions."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('stage_roster_base',ROOT/'research/verify-world-roster-regression-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross,real=base.suite,base.cross,base.real
from portable_squad_stage_roster_cases import fixtures
from portable_real_burst_policy import configured


def prepare():
    entries=[]
    for case in fixtures():
        with configured(case['body'],case.get('burst_stages',{}),case.get('live_overrides',())):prepared=real.engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,metadata=real.compile_projectile_battle(prepared)
        entries.append((case['name'],words,(case,prepared,words,metadata)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    case=domain[0]
    with configured(case['body'],case.get('burst_stages',{}),case.get('live_overrides',())):native,shots=real.native_reference(case['body'])
    owners=[x['event'] for x in native['burst_trace'] if x['owner']==0 and x['event'] in (1,2,3)]
    assert set(owners)==({1,2,3} if case.get('burst_stages') or case.get('live_overrides') and case['live_overrides'][0]['duration']==-1 else {3}),(case['name'],'all native role branches',owners)
    return dict(battle=native,physical_shots=shots)


def compare(block,domain):
    case,prepared,words,metadata=domain;expected=native_reference(domain)
    _,_,omitted,differences=real.compare(block,prepared,(words,metadata),expected['battle'],expected['physical_shots'])
    assert block[0]==0 and not differences,(case['name'],'full original Red Hood',differences[:8])
    return expected


def validate_rejection(block,name):raise AssertionError('No raw rejections in complete Red Hood suite')
