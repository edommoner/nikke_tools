"""Actual fire returns and landed logical actors in the opt-in producer."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
import copy
import engine_worker
from battle_attack_group_runtime import battle_attack_groups
from effect_runtime import state
from impact_specs import ActorKind
def handle(h):return [int(h.kind),h.identity,h.generation]
def observe(case):
    s=importlib.util.spec_from_file_location('shot_group_roster_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
    from calculator.buff_manager import BuffManager
    previous=BuffManager._register_all
    def register(manager):
        result=previous(manager)
        for effect in case.get('declared_effects',[]):manager._effects.append((copy.deepcopy(effect),case['body']['squad'][0]))
        manager._build_notify_index()
        return result
    with patch.object(BuffManager,'_register_all',register),battle_attack_groups(routing=case['routing']) as data:n,shots=r.native_reference(case['body'])
    assert len(data['managers'])==1;manager=data['managers'][0];runtime=state(manager);boss,registry=runtime.world_actor_registry
    assert not runtime.event_stack and not runtime.impact_stack and not runtime.activation_stack
    for name in ('attack_groups','sealed_attack_groups','dispatching_attack_groups'):assert not runtime.resources.get(name)
    groups=[dict(g,targets=[handle(h) for h in g['targets']]) for g in data['groups']]
    notices=[dict(g,key=[g['key'].caster,g['key'].identity,g['key'].epoch],targets=[handle(h) for h in g['targets']]) for g in data['notifications']]
    children=[dict(g,targets=[handle(h) for h in g['targets']]) for g in data['children']]
    child_landings=[dict(g,target=handle(g['target'])) for g in data['child_landings']]
    adds=[]
    for run in boss._runs:
        for actor in run.adds:
            h=registry.view(ActorKind.ADD,actor.id).handle;adds.append(dict(label=actor.id,handle=handle(h),alive=actor.alive,dealt=actor.dealt,hits=actor.hits))
    fields=[]
    for ab in manager._active:
        key=getattr(ab,'enemy_recipient_key',None)
        if key is not None:fields.append(dict(name=ab.effect.get('name'),owner=ab.caster,targets=list(ab.target_chars or []),handles=[handle(x.actor) for x in key.bindings]))
    return dict(battle=n,projectile_shots=shots,shots=data['shots'],groups=groups,notifications=notices,children=children,child_landings=child_landings,adds=adds,fields=fields,add_damage=dict(boss.add_dealt),add_overkill=boss.add_overkill),[]
