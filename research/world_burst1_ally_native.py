"""Observe existing condition returns and live stage snapshots without queries."""
import engine_worker
from unittest.mock import patch
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain

def observe(case):
    names=roster_names(case);original=BuffManager._condition_ok;rows=[]
    def condition(bm,conditions,caster,t,eff=None):
        selected=eff is not None and eff.get('name')=='burst1-listener'
        if selected:row=dict(owner=names.index(caster),time=t,conditions=list(conditions),stages=[bm.state.get('burst_stages',{}).get(n) for n in names],down=[i for i,n in enumerate(names) if n in bm.state.get('down',set())])
        result=original(bm,conditions,caster,t,eff)
        if selected:row['result']=result;rows.append(row)
        return result
    with patch.object(BuffManager,'_condition_ok',condition):n,t=plain(case)
    n['burst1_ally_conditions']=rows;return n,t
