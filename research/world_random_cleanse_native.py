"""Snapshot actual native cleanse dispatches without additional queries."""
import random
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain


def observe(case):
    names=roster_names(case);calls=[];samples=[]
    dispatch=BuffManager._dispatch_instant;sample=random.sample
    def snapshot(bm):
        return {ab.effect['name']:[names.index(n) for n in ab.target_chars or []] for ab in bm._active}
    def sampled(pool,k,**kw):
        before=random.getstate();picked=sample(pool,k,**kw);after=random.getstate()
        samples.append(dict(pool=[names.index(n) for n in pool],picked=[names.index(n) for n in picked],k=k,before_index=before[1][-1],after_index=after[1][-1],state_changed=before!=after))
        return picked
    def dispatched(bm,eff,caster,t,from_tick=False):
        if eff.get('name')!='random-cleanse':return dispatch(bm,eff,caster,t,from_tick=from_tick)
        row=dict(owner=names.index(caster),time=t,before=snapshot(bm));result=dispatch(bm,eff,caster,t,from_tick=from_tick)
        row['after']=snapshot(bm);calls.append(row);return result
    with patch.object(random,'sample',sampled),patch.object(BuffManager,'_dispatch_instant',dispatched):native,trace=plain(case)
    native['random_cleanse']=dict(calls=calls,samples=samples)
    return native,trace
