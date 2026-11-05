"""Observe actual ranking callbacks and sentinel resolutions, without queries."""
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from calculator.boss_pattern import BossScript
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names):
    rankings=[];recipients=[];ranked=BossScript._ranked;resolve=BuffManager._resolve_enemies
    def selected(target):return isinstance(target,str) and target.startswith('enemies_with_buff:')
    def rank(boss,target,has_state,caster=''):
        if not selected(target):return ranked(boss,target,has_state,caster)
        checks=[]
        def checked(identity,name):
            answer=has_state(identity,name);checks.append(dict(identity=identity,name=name,present=answer));return answer
        answer=ranked(boss,target,checked if has_state is not None else None,caster)
        rankings.append(dict(target=target,owner=names.index(caster),checks=checks,order=list(answer[0]),count=answer[1]));return answer
    def resolved(bm,target,caster=''):
        answer=resolve(bm,target,caster)
        if selected(target):recipients.append(dict(target=target,owner=names.index(caster),time=bm._cur_t,picked=list(answer)))
        return answer
    with patch.object(BossScript,'_ranked',rank),patch.object(BuffManager,'_resolve_enemies',resolved):yield dict(rankings=rankings,recipients=recipients)

def observe(case):
    with capture(roster_names(case)) as observed:n,t=plain(case)
    n['named_enemy']=observed;return n,t
