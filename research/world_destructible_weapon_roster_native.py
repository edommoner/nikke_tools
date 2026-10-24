"""Original roster simulation under the explicit typed weapon policy only."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
import engine_worker
from destructible_battle_runtime import typed_battle
from destructible_shield_policy import BOSS
from impact_specs import ActorKind
import destructible_damage_policy

def observe(case):
    s=importlib.util.spec_from_file_location('weapon_shield_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));roster=importlib.util.module_from_spec(s);s.loader.exec_module(roster)
    from calculator.buff_manager import BuffManager
    heals=[];original_heal=BuffManager.apply_shared_body_heal
    def heal(manager,name,amount,t):
        before=manager.state['hp'][name];value=original_heal(manager,name,amount,t)
        heals.append(dict(owner=case['body']['squad'].index(name),time=t,amount=amount,before=before,after=manager.state['hp'][name]))
        return value
    samples=[];original=destructible_damage_policy.calculate
    def calculate(*args,**kw):
        value=original(*args,**kw)
        if kw['kind']==ActorKind.HP_SHIELD or case.get('skill_shield_interception_v1'):
            buffs=kw.get('buffs',args[1] if len(args)>1 else {})
            row=dict(modifier=buffs.get('shield_dmg_pct',0.),factor5=value['factor5'],damage=value['damage'])
            if case.get('skill_shield_interception_v1'):row.update(scalar_kind=int(kw['kind']),applied_modifier=buffs.get('shield_dmg_pct',0.) if kw['kind']==ActorKind.HP_SHIELD else 0.)
            if case.get('skill_shield_interception_v1'):
                hit=kw.get('hit_type',args[3] if len(args)>3 else {})
                row['family_flags']={k:bool(hit.get(k,False)) for k in ('is_burst_damage','is_aoe_burst','is_single_burst')}
            samples.append(row)
        return value
    with typed_battle(case['typed_bindings'],modifier_model=True,shield_owner=BOSS,hit_shields=True,weapon_shields=True,max_attacks=case['max_attacks'],skill_shields=case.get('skill_shield_interception_v1',False)) as data,patch.object(destructible_damage_policy,'calculate',calculate),patch.object(BuffManager,'apply_shared_body_heal',heal):
        battle,shots=roster.native_reference(case['body'])
    assert len(data['worlds'])==len(data['managers'])==1
    from effect_runtime import state
    runtime=state(data['managers'][0]);assert not runtime.event_stack and not runtime.impact_stack and not runtime.activation_stack
    world=data['worlds'][0];names=case['body']['squad'];targets=[]
    for r in world.targets.rows:
        targets.append(None if r is None else dict(handle=[int(r.handle.kind),r.handle.identity,r.handle.generation],alive=r.alive,remaining=r.remaining,capacity=r.capacity,expires=r.expires,owner=None if r.owner is None else [int(r.owner.kind),r.owner.identity,r.owner.generation]))
    attacks=[]
    for r in data['attacks']:
        if not case.get('skill_shield_interception_v1'):assert 'family' in r,'Weapon-only roster must not silently intercept skill packets'
        attacks.append(dict(attack_id=r['attack_id'],owner=names.index(r['caster']),time=r['time'],damage=r['damage'],completed=r['completed'],receipts=[dict(slot=slot,handle=[int(h.kind),h.identity,h.generation],delivered=v['delivered'],broken=v['broken'],took=v['took']) for slot,h,v in r['receipts']]))
    samples_expected=[r['damage'] for r in attacks];assert [r['damage'] for r in samples]==samples_expected
    result=dict(battle=battle,projectile_shots=shots,typed=dict(time=world.last,finished=world.finished,state=targets,attacks=attacks),shield_samples=samples,healing=heals)
    if case.get('skill_shield_interception_v1'):
        packets=[]
        for r in data['attacks']:
            source=None
            if 'family' not in r:
                matches=[i for i,(effect,caster) in enumerate(data['managers'][0]._effects) if effect.get('name')==r['name'] and caster==r['caster']]
                assert len(matches)==1,'Unambiguous original skill definition required';source=matches[0]
            packets.append(dict(coefficient=r['coefficient'],mode_skill=r.get('weapon_mode_skill',False),source=source,name=r['name']))
        result['packet_samples']=packets
    else:result['weapon_samples']=[dict(coefficient=r['coefficient'],mode_skill=r['weapon_mode_skill']) for r in data['attacks']]
    return result,[]
