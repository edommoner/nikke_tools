"""Observe actual handler entries, native count reads and callbacks without queries."""
import sys
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names):
    calls=[];counts=[];hits=[];selected=set();old=sys.getprofile();notify=BuffManager.notify
    def prof(frame,event,result):
        if old is not None:old(frame,event,result)
        if frame.f_code.co_name=='_handle_damage_eff' and event=='call':
            eff=frame.f_locals.get('eff',{});bm=frame.f_locals.get('bm')
            if 'land_in_full_burst' in eff:
                selected.add(eff['name']);calls.append(dict(name=eff['name'],time=frame.f_locals['t'],owner=names.index(frame.f_locals['caster']),resolved=bool(eff.get('_landing_resolved')),latched=eff.get('_latched_hit_count'),full=bool(bm.state.get('full_burst')),excluded=sorted(eff.get('_exclude_buffs',()))))
        if frame.f_code.co_name=='live_reference' and frame.f_globals.get('__name__')=='reference_count_runtime' and event=='return' and frame.f_locals.get('ref') in ('cast-count','missing'):
            counts.append(dict(name=frame.f_locals['ref'],value=result,caller=frame.f_back.f_code.co_name))
    def notified(bm,event,t,caster,**ctx):
        if event.startswith('hit_count:') and event[len('hit_count:'):] in selected:hits.append(dict(name=event[len('hit_count:'):],time=t,owner=names.index(caster),full=bool(bm.state.get('full_burst'))))
        return notify(bm,event,t,caster,**ctx)
    with patch.object(BuffManager,'notify',notified):
        sys.setprofile(prof)
        try:yield dict(calls=calls,count_reads=counts,hits=hits)
        finally:sys.setprofile(old)
def observe(case):
    with capture(roster_names(case)) as o:n,t=plain(case)
    o['packets']=t;n['full_burst_landing']=o;return n,t
