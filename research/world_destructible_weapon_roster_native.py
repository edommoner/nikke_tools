"""Original roster simulation under the explicit typed weapon policy only."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager
import engine_worker
from destructible_battle_runtime import typed_battle
from destructible_shield_policy import BOSS
from impact_specs import ActorKind
import destructible_damage_policy

@contextmanager
def capture_typed(case):
    from calculator.buff_manager import BuffManager
    heals=[];original_heal=BuffManager.apply_shared_body_heal
    def heal(manager,name,amount,t):
        before=manager.state['hp'][name];value=original_heal(manager,name,amount,t)
        heals.append(dict(owner=case['body']['squad'].index(name),time=t,amount=amount,before=before,after=manager.state['hp'][name]))
        return value
    samples=[];original=destructible_damage_policy.calculate
    def calculate(*args,**kw):
        value=original(*args,**kw)
        if kw['kind']==ActorKind.HP_SHIELD or case.get('skill_shield_interception_v1') or (case.get('declared_projectile_probe') or case.get('coordinate_weapon_targets')) and kw['kind']==ActorKind.PROJECTILE:
            buffs=kw.get('buffs',args[1] if len(args)>1 else {})
            row=dict(modifier=buffs.get('projectile_dmg_pct' if (case.get('declared_projectile_probe') or case.get('coordinate_weapon_targets')) and kw['kind']==ActorKind.PROJECTILE else 'shield_dmg_pct',0.),factor5=value['factor5'],damage=value['damage'])
            if case.get('coordinate_weapon_targets'):row['scalar_kind']=int(kw['kind'])
            if case.get('declared_projectile_probe'):row['shield_modifier']=buffs.get('shield_dmg_pct',0.)
            if case.get('declared_projectile_probe') and case.get('probe_kind')==3:row['projectile_modifier']=buffs.get('projectile_dmg_pct',0.)
            if case.get('skill_shield_interception_v1'):row.update(scalar_kind=int(kw['kind']),applied_modifier=buffs.get('shield_dmg_pct',0.) if kw['kind']==ActorKind.HP_SHIELD else 0.)
            if case.get('skill_shield_interception_v1'):
                hit=kw.get('hit_type',args[3] if len(args)>3 else {})
                row['family_flags']={k:bool(hit.get(k,False)) for k in ('is_burst_damage','is_aoe_burst','is_single_burst')}
            samples.append(row)
        return value
    physical=case.get('coordinate_weapon_targets',False)
    probe=case.get('declared_projectile_probe',False)
    with typed_battle(case['typed_bindings'],modifier_model=True,shield_owner=None if physical or probe and case.get('probe_kind',2)==2 else BOSS,hit_shields=not (probe or physical),weapon_shields=not (probe or physical),max_attacks=case['max_attacks'],skill_shields=case.get('skill_shield_interception_v1',False),body_lifesteal=case.get('body_lifesteal_v1',False),body_accumulation=case.get('body_accumulation_v1',False),typed_geometry=case.get('typed_geometry'),coordinate_weapon_targets=physical,typed_aim_policy=case.get('typed_aim_policy'),typed_actor_policy=case.get('typed_actor_policy')) as data,patch.object(destructible_damage_policy,'calculate',calculate),patch.object(BuffManager,'apply_shared_body_heal',heal):
        yield data,samples,heals

def snapshot_typed(case,data,samples,heals,battle,shots):
    assert len(data['worlds'])==len(data['managers'])==1
    from effect_runtime import state
    runtime=state(data['managers'][0]);assert not runtime.event_stack and not runtime.impact_stack and not runtime.activation_stack
    world=data['worlds'][0];names=case['body']['squad'];targets=[]
    for r in world.targets.rows:
        targets.append(None if r is None else dict(handle=[int(r.handle.kind),r.handle.identity,r.handle.generation],alive=r.alive,remaining=r.remaining,capacity=r.capacity,expires=r.expires,owner=None if r.owner is None else [int(r.owner.kind),r.owner.identity,r.owner.generation]))
    attacks=[]
    for r in data['attacks']:
        if not case.get('skill_shield_interception_v1') and not case.get('declared_projectile_probe'):assert 'family' in r,'Weapon-only roster must not silently intercept skill packets'
        attacks.append(dict(attack_id=r['attack_id'],owner=names.index(r['caster']),time=r['time'],damage=r['damage'],completed=r['completed'],receipts=[dict(slot=slot,handle=[int(h.kind),h.identity,h.generation],delivered=v['delivered'],broken=v['broken'],took=v['took']) for slot,h,v in r['receipts']]))
    if case.get('body_accumulation_v1'):
        scalar=iter(samples);ordered=[]
        for raw,row in zip(data['attacks'],attacks,strict=True):
            if raw.get('quantity_only'):
                ordered.append(dict(modifier=0.,factor5=None,damage=row['damage'],scalar_kind=raw['receipts'][0][1].kind.value,applied_modifier=0.,family_flags=dict(is_burst_damage=False,is_aoe_burst=False,is_single_burst=False)))
            else:ordered.append(next(scalar))
        assert next(scalar,None) is None;samples=ordered
    samples_expected=[r['damage'] for r in attacks];assert [r['damage'] for r in samples]==samples_expected
    result=dict(battle=battle,projectile_shots=shots,typed=dict(time=world.last,finished=world.finished,state=targets,attacks=attacks),healing=heals)
    result['modifier_samples' if case.get('declared_projectile_probe') else 'shield_samples']=samples
    if case.get('skill_shield_interception_v1') or case.get('declared_projectile_probe'):
        packets=[]
        for r in data['attacks']:
            source=None
            if 'family' not in r:
                matches=[i for i,(effect,caster) in enumerate(data['managers'][0]._effects) if effect.get('name')==r['name'] and caster==r['caster']]
                assert len(matches)==1,'Unambiguous original skill definition required';source=matches[0]
            packet=dict(coefficient=r['coefficient'],mode_skill=r.get('weapon_mode_skill',False),source=source,name=r['name'])
            if r.get('quantity_only'):packet['quantity_only']=True
            packets.append(packet)
        result['packet_samples']=packets
    else:result['weapon_samples']=[dict(coefficient=r['coefficient'],mode_skill=r['weapon_mode_skill']) for r in data['attacks']]
    return result

def observe(case):
    s=importlib.util.spec_from_file_location('weapon_shield_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));roster=importlib.util.module_from_spec(s);s.loader.exec_module(roster)
    from calculator.buff_manager import BuffManager
    with capture_typed(case) as (data,samples,heals):
        if case.get('declared_effects'):
            previous_effects=BuffManager._register_all
            def register_extra(manager):
                result=previous_effects(manager)
                import copy
                for effect in case['declared_effects']:manager._effects.append((copy.deepcopy(effect),case.get('probe_owner',case['body']['squad'][0])))
                manager._build_notify_index()
                return result
            with patch.object(BuffManager,'_register_all',register_extra):battle,shots=roster.native_reference(case['body'])
        else:battle,shots=roster.native_reference(case['body'])
    return snapshot_typed(case,data,samples,heals,battle,shots),[]
