"""Observe shield receipts alongside the unchanged native battle result."""
import engine_worker
from destructible_battle_runtime import typed_battle
from destructible_shield_policy import BOSS
from world_frame_native import observe as battle

def observe(case):
    with typed_battle(case['typed_bindings'],modifier_model=True,shield_owner=BOSS) as data:
        native=battle(case)
    from effect_runtime import state
    manager,=data['managers'];runtime=state(manager)
    assert not runtime.event_stack and not runtime.impact_stack and not runtime.activation_stack
    world,=data['worlds']
    attacks=[]
    for row in data['attacks']:
        attacks.append(dict(damage=row['damage'],coefficient=row['coefficient'],completed=row['completed'],time=row['time'],receipts=[dict(slot=slot,handle=[int(h.kind),h.identity,h.generation],delivered=r['delivered'],broken=r['broken'],took=r['took']) for slot,h,r in row['receipts']]))
    answer=dict(battle=native,attacks=attacks,remaining=[None if row is None else row.remaining for row in world.targets.rows],alive=[False if row is None else row.alive for row in world.targets.rows],finished=world.finished)
    return answer,[]
