"""Observe real charge readers and RNG; never issue extra numeric queries."""
import sys,hashlib,json
from calculator import timeline
from world_nonfull_charge_native import observe as charge_observe
from world_late_attack_random_native import capture_queries
from world_frame_native import roster_names


def observe(case):
    names=roster_names(case);reads=[];active={};previous=sys.getprofile()
    code=timeline.CharState._effective_charge_time.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if frame.f_code is not code:return
        if event=='call':
            who=frame.f_locals['self'];active[id(frame)]=len(reads)
            reads.append(dict(owner=names.index(who.name),time=frame.f_locals['t'],phase=who._charge_phase,tap=bool(getattr(who,'_tap_this_shot',False)),force_full=bool(getattr(who,'_force_full_charge',False))))
        elif event=='return':reads[active.pop(id(frame))]['value']=answer
    sys.setprofile(profile)
    try:
        with capture_queries(names,with_selectors=True) as (queries,samples):native,trace=charge_observe(case)
    finally:sys.setprofile(previous)
    assert not active
    native['partial_query']=dict(reads=reads,queries=queries,samples=samples,trace_sha256=hashlib.sha256(json.dumps(trace,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
    return native,trace
