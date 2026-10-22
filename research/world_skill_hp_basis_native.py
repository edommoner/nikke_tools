"""Observe actual native HP-basis queries and existing landed-packet boundaries."""
import sys
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_parts_skill_native import observe as parts_observe

def observe(case):
    names=roster_names(case);queries=[];errors=[];previous=sys.getprofile();code=BuffManager.effective_max_hp.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='return' or frame.f_code is not code:return
        caller=frame.f_back
        if caller is None or caller.f_code.co_name!='_handle_damage_eff' or caller.f_locals.get('eff',{}).get('name')!='parts-source':return
        try:queries.append(dict(owner=names.index(frame.f_locals['name']),time=caller.f_locals['t'],maximum=answer))
        except (KeyError,ValueError,TypeError) as error:errors.append(str(error))
    sys.setprofile(profile)
    try:native,trace=parts_observe(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Native HP-basis observation failed: '+str(errors))
    native['skill_hp_basis_queries']=queries
    return native,trace
