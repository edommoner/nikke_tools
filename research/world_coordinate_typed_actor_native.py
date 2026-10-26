"""Passive canonical logical-enemy choices, with unmodified original skills."""
import sys
from contextlib import contextmanager
from unittest.mock import patch
from portable_coordinate_typed_weapon_cases import prepare
from world_coordinate_typed_aim_native import observe as aims

@contextmanager
def capture():
    from calculator import timeline
    original=timeline.BossScript._aim_enemy;rows=[]
    def choose(boss,caster):
        result=original(boss,caster);frame=sys._getframe(1);event=None
        for _ in range(3):
            if frame is None:break
            if 'ev' in frame.f_locals:event=frame.f_locals['ev'];break
            frame=frame.f_back
        world=getattr(boss,'_nikke_typed_world',None)
        rows.append(dict(time=getattr(event,'t',world.last if world is not None else None),caster=caster,aim=boss.aim_of.get(caster,''),logical=result,skill=getattr(event,'skill_name',''),rule=getattr(event,'rule',''),caller=sys._getframe(1).f_code.co_name))
        return result
    with patch.object(timeline.BossScript,'_aim_enemy',choose):yield rows

def observe(row):
    case=row if 'original_run' in row else prepare(row)[0]
    with capture() as rows:n,trace=aims(case)
    n['coordinate_typed_actor_queries']=rows
    return n,trace
