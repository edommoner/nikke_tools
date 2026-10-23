"""Read the actual final deferred list; no synthetic replay or reference queries."""
import sys,types
from contextlib import contextmanager
from calculator import timeline
from world_frame_native import roster_names
from world_full_burst_queue_native import observe as plain

@contextmanager
def final_queue(names):
    codes=[c for c in timeline.simulate.__code__.co_consts if isinstance(c,types.CodeType) and c.co_name=='_handle_damage_eff']
    if len(codes)!=1:raise ValueError('Native deferred handler missing or ambiguous')
    old=sys.getprofile();controllers=[];out={}
    def profile(frame,event,result):
        if old is not None:old(frame,event,result)
        if frame.f_code is codes[0] and event=='call':
            ctrl=frame.f_locals['burst_ctrl']
            if not controllers:controllers.append(ctrl)
            elif controllers[0] is not ctrl:raise ValueError('Native controller identity changed')
    sys.setprofile(profile)
    try:
        yield out
        if len(controllers)!=1:raise ValueError('Native deferred queue not observed')
        out['entries']=[dict(owner=names.index(caster),name=eff['name'],hits=eff['_latched_hit_count']) for caster,eff in controllers[0]._pending_landing_dmg]
    finally:sys.setprofile(old)

def observe(case):
    with final_queue(roster_names(case)) as q:n,t=plain(case)
    n['full_burst_capacity']=q;return n,t
