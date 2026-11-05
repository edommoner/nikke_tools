"""Snapshot actual native cleanse dispatches without additional queries."""
import random,hashlib,json
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain


@contextmanager
def capture(names):
    calls=[];samples=[];seeds=[]
    dispatch=BuffManager._dispatch_instant;sample=random.sample;seed=random.seed
    digest=lambda state:hashlib.sha256(json.dumps(state,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    def seeded(*a,**kw):
        result=seed(*a,**kw);seeds.append(digest(random.getstate()));return result
    def snapshot(bm):
        return {ab.effect['name']:[names.index(n) for n in ab.target_chars or []] for ab in bm._active}
    def sampled(pool,k,**kw):
        before=random.getstate();picked=sample(pool,k,**kw);after=random.getstate()
        samples.append(dict(pool=[names.index(n) for n in pool],picked=[names.index(n) for n in picked],k=k,before_index=before[1][-1],after_index=after[1][-1],state_changed=before!=after,before_sha256=digest(before),after_sha256=digest(after)))
        return picked
    def dispatched(bm,eff,caster,t,from_tick=False):
        if eff.get('stat')!='debuff_cleanse' or not str(eff.get('target','')).startswith('allies_random_with_debuff:'):return dispatch(bm,eff,caster,t,from_tick=from_tick)
        row=dict(owner=names.index(caster),time=t,before=snapshot(bm),down=[i for i,n in enumerate(names) if n in bm.state.get('down',())]);result=dispatch(bm,eff,caster,t,from_tick=from_tick)
        row['after']=snapshot(bm);calls.append(row);return result
    with patch.object(random,'seed',seeded),patch.object(random,'sample',sampled),patch.object(BuffManager,'_dispatch_instant',dispatched):yield dict(calls=calls,samples=samples,seed_sha256=seeds)

def observe(case):
    with capture(roster_names(case)) as observation:native,trace=plain(case)
    native['random_cleanse']=observation
    return native,trace
