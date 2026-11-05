"""Read each native sample once, preserving separate global/boss random streams."""
import hashlib,json,random
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain_observe


def observe(case):
    names=roster_names(case);rows=[];resolutions=[];sample=random.sample;resolve=BuffManager._resolve_target_raw
    def sampled(pool,k,**kwargs):
        before=random.getstate();answer=sample(pool,k,**kwargs);after=random.getstate()
        rows.append(dict(pool=[names.index(n) for n in pool],k=k,picked=[names.index(n) for n in answer],before_index=before[1][-1],after_index=after[1][-1],before_sha256=hashlib.sha256(json.dumps(before,separators=(',',':'),allow_nan=False).encode()).hexdigest(),after_sha256=hashlib.sha256(json.dumps(after,separators=(',',':'),allow_nan=False).encode()).hexdigest()))
        return answer
    def resolved(bm,target,caster):
        answer=resolve(bm,target,caster)
        if isinstance(target,str) and target.startswith(('allies_random:','allies_broken_cover_random:')):resolutions.append(dict(target=target,caster=names.index(caster),picked=[names.index(n) for n in answer]))
        return answer
    with patch.object(random,'sample',sampled),patch.object(BuffManager,'_resolve_target_raw',resolved):native,trace=plain_observe(case)
    native['ally_random_reference']=dict(samples=rows,resolutions=resolutions)
    return native,trace
