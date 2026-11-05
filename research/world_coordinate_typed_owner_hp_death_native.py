"""Passive before/after witnesses around the existing canonical ADD damage call."""
from unittest.mock import patch
from portable_coordinate_typed_owner_hp_death_cases import prepare
from world_coordinate_typed_owner_add_lifetime_native import observe as lifetime

def observe(row):
    from calculator.boss_pattern import BossScript
    c=row if 'original_run' in row else prepare(row)[0];original=BossScript.hit_add;hits=[]
    def hit(clock,event,add_id,t):
        rows=[(run,add) for run in clock._runs for add in run.adds if add.id==add_id]
        def state():
            return [dict(alive=add.alive,dealt=add.dealt,hp=add.spec.hp,hit_hp=add.spec.hit_hp,
                         graph_active=run.active,generation=run.opens) for run,add in rows]
        before=state();result=original(clock,event,add_id,t);after=state()
        hits.append(dict(time=float(t),label=add_id,damage=float(event.damage),before=before,after=after,accepted=result))
        return result
    with patch.object(BossScript,'hit_add',hit):native,trace=lifetime(c)
    native['owner_hp_death']=dict(hits=hits)
    return native,trace
