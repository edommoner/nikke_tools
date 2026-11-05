"""Observe original pre-weapon aim state; do not issue extra buff/aim queries."""
from unittest.mock import patch
import engine_worker
from calculator import timeline
from world_projectile_native import observe as plain_observe
from world_frame_native import roster_names


def observe(case):
    names=roster_names(case);rows=[];tick=timeline.CharState.tick
    def ticking(actor,t,bm,enemy,cfg):
        if not rows or rows[-1]['time']!=t:
            rows.append(dict(time=t,aims=[bm.state.get('aim',{}).get(n,(None,''))[1] for n in names],
                             camera=sum(1<<i for i,n in enumerate(names) if n in bm.state.get('camera',())),
                             full_burst=bool(bm.state.get('full_burst'))))
        return tick(actor,t,bm,enemy,cfg)
    with patch.object(timeline.CharState,'tick',ticking):native,trace=plain_observe(case)
    native['focus_aim']=rows
    return native,trace
