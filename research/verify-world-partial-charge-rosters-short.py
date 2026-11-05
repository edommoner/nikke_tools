"""All real Crust effects, actual partial/full shots and unchanged comparator."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('partial_roster_base',ROOT/'research/verify-world-roster-regression-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross,real=base.suite,base.cross,base.real
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_partial_charge_roster_cases import fixtures
from portable_real_shooting_policy import configured
from portable_partial_charge_state import validate_state
from portable_specs import LIMITS as L
from portable_charge_control_specs import WORDS as CONTROL_WORDS


def prepare():
    entries=[]
    for case in fixtures():
        with configured(case['body'],case['shooting_controls']):prepared=real.engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,metadata=real.compile_projectile_battle(prepared)
        entries.append((case['name'],words,(case,prepared,words,metadata)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    case=domain[0];events=[];previous=sys.getprofile();shot_code=timeline.CharState._charge_fire.__code__;notify_code=BuffManager.notify.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='call':return
        v=frame.f_locals
        if frame.f_code is shot_code and v['self'].name=='크러스트':events.append(dict(kind='shot',time=v['t'],full=v['is_full']))
        elif frame.f_code is notify_code and v['caster']=='크러스트' and v['event'] in ('non_full_charge_fire','full_charge_fire'):events.append(dict(kind=v['event'],time=v['t']))
    sys.setprofile(profile)
    try:
        with configured(case['body'],case['shooting_controls']):native,shots=real.native_reference(case['body'])
    finally:sys.setprofile(previous)
    partial=[e for e in events if e['kind']=='shot' and not e['full']];full=[e for e in events if e['kind']=='shot' and e['full']]
    assert [e['time'] for e in partial]==[e['time'] for e in events if e['kind']=='non_full_charge_fire'],case['name']
    assert [e['time'] for e in full]==[e['time'] for e in events if e['kind']=='full_charge_fire'],case['name']
    assert len(partial)>=3 if case['shooting_controls'] else len(partial)==0,case['name']
    return dict(battle=native,physical_shots=shots,partial_receipts=events)


def compare(block,domain):
    case,prepared,words,metadata=domain;validate_state(block,words[L['WORLD_CONTROL_INPUT_BASE']:L['WORLD_CONTROL_INPUT_BASE']+CONTROL_WORDS]);expected=native_reference(domain)
    _,_,omitted,differences=real.compare(block,prepared,(words,metadata),expected['battle'],expected['physical_shots'])
    assert block[0]==0 and not differences,(case['name'],'full original Crust',differences[:8])
    return expected


def validate_rejection(block,name):raise AssertionError('No raw rejections in complete Crust suite')
