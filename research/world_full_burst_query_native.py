"""Capture real handler-local buff/ref/HP returns in order without extra queries."""
import sys
from calculator.buff_manager import BuffManager
from world_full_burst_landing_native import observe as plain

def observe(case):
    events=[];old=sys.getprofile();get=BuffManager.get_buffs.__code__;ref=BuffManager.ref_count.__code__;hp=BuffManager.effective_max_hp.__code__
    def profile(frame,event,value):
        if old is not None:old(frame,event,value)
        if event!='return' or frame.f_code not in (get,ref,hp):return
        caller=frame.f_back
        if caller is None or caller.f_code.co_name!='_handle_damage_eff':return
        eff=caller.f_locals.get('eff',{})
        if eff.get('name')!='landing' or not eff.get('_landing_resolved'):return
        row=dict(kind=1 if frame.f_code is get else 2 if frame.f_code is ref else 3,time=caller.f_locals['t'])
        if row['kind']==1:row.update(flat=value.get('atk_flat',0),percent=value.get('atk_pct',0))
        elif row['kind']==2:row.update(present=value is not None,value=value if value is not None else 0)
        else:row.update(maximum=value)
        events.append(row)
    sys.setprofile(profile)
    try:n,t=plain(case)
    finally:sys.setprofile(old)
    n['full_burst_query']=events;return n,t
