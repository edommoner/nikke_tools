"""Observe original condition/cover/camera queries without extra resolutions."""
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain_observe


@contextmanager
def capture_queries(names):
    checks=[];runtime=[];stack=[];managers=[]
    condition=BuffManager._condition_ok;cover=BuffManager.cover_alive;query=BuffManager._runtime_condition_ok
    def checked(bm,conditions,caster,t,eff=None):
        if not eff or eff.get('name')!='state-witness':return condition(bm,conditions,caster,t,eff)
        managers[:]=[bm];row=dict(owner=names.index(caster),time=t,cover=[]);checks.append(row);stack.append(row)
        try:row['result']=bool(condition(bm,conditions,caster,t,eff));return row['result']
        finally:stack.pop()
    def covered(bm,name):
        result=cover(bm,name)
        if stack:stack[-1]['cover'].append(dict(owner=names.index(name),result=bool(result)))
        return result
    def runtime_checked(bm,conditions,buff_caster,query_target,target,t):
        result=query(bm,conditions,buff_caster,query_target,target,t)
        if 'focusing' in conditions:runtime.append(dict(owner=names.index(buff_caster),query_target=query_target,time=t,camera_mask=sum(1<<names.index(n) for n in bm.state.get('camera',())),result=bool(result)))
        return result
    with patch.object(BuffManager,'_condition_ok',checked),patch.object(BuffManager,'cover_alive',covered),patch.object(BuffManager,'_runtime_condition_ok',runtime_checked):yield checks,runtime,managers


def observe(case):
    names=roster_names(case)
    with capture_queries(names) as (checks,runtime,managers):native,trace=plain_observe(case)
    bm=managers[0];carriers=[dict(owner=names.index(a.caster),stack=a.stack) for a in bm._active if a.effect.get('name')=='state-witness']
    native['state_predicates']=dict(checks=checks,runtime=runtime,carriers=carriers)
    return native,trace
