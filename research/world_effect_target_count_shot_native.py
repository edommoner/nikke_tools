"""Transparent observations around actual native physical-shot consumption."""
import copy
from unittest.mock import patch
from calculator.buff_manager import BuffManager,_is_bullet_bound_trigger
from effect_target_count_policy import MODEL,STAT,query
from world_frame_native import roster_names
from world_projectile_native import observe as baseline

def state(manager,caster,when):
    q=query(manager,caster,'록 온',when,base_count=5,capacity_limit=128,model=MODEL)
    rows=[ab for ab in manager._active if ab.effect.get('stat')==STAT and ab.effect.get('target_effect')=='록 온']
    if len(rows)>1:raise ValueError('Shot observation requires one named carrier')
    ab=rows[0] if rows else None
    remaining=0 if ab is None else ab.bullets_per_target.get(caster,ab.bullets_left if ab.caster==caster and ab.bullets_left>=0 else 0)
    return dict(capacity=q['capacity'],additional=q['additional_targets'],remaining=remaining,present=ab is not None,
        activated=ab.activated_at if ab is not None else 0.,skipped=bool(remaining and ab.activated_at==when and not _is_bullet_bound_trigger(ab.effect)))

def observe(case):
    before=copy.deepcopy(case);events=[];names=roster_names(case);consume=BuffManager.consume_bullet_buffs
    def consumed(manager,caster,t=0.):
        previous=state(manager,caster,t);answer=consume(manager,caster,t);after=state(manager,caster,t)
        events.append(dict(who=names.index(caster),time=t,before=previous,after=after));return answer
    with patch.object(BuffManager,'consume_bullet_buffs',consumed):native,trace=baseline(case)
    plain,plain_trace=baseline(case)
    if native!=plain or trace!=plain_trace or case!=before:raise AssertionError('Shot queries changed complete native battle/trace/input')
    return dict(battle=native,skill_trace=trace,target_count_shots=events)
