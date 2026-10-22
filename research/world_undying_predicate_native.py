"""Record original has_live_stat calls exactly once; do not query extra state."""
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain_observe


@contextmanager
def capture_queries(names,effect_name):
    checks=[];stack=[];managers=[]
    original=BuffManager._condition_ok;live=BuffManager.has_live_stat
    def condition(bm,conditions,caster,t,eff=None):
        if not eff or eff.get('name')!=effect_name:return original(bm,conditions,caster,t,eff)
        managers[:]=[bm];row=dict(owner=names.index(caster),time=t,queries=[]);checks.append(row);stack.append(row)
        try:row['result']=bool(original(bm,conditions,caster,t,eff));return row['result']
        finally:stack.pop()
    def queried(bm,owner,stat,t):
        result=live(bm,owner,stat,t)
        if stack:stack[-1]['queries'].append(dict(owner=names.index(owner),stat=stat,time=t,result=bool(result)))
        return result
    with patch.object(BuffManager,'_condition_ok',condition),patch.object(BuffManager,'has_live_stat',queried):yield checks,managers


def observe(case):
    names=roster_names(case)
    with capture_queries(names,'undying-witness') as (checks,managers):native,trace=plain_observe(case)
    bm=managers[0];carriers=[dict(owner=names.index(a.caster),stack=a.stack) for a in bm._active if a.effect.get('name')=='undying-witness']
    native['undying_predicate']=dict(checks=checks,carriers=carriers)
    return native,trace
