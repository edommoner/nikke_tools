"""Readiness evidence from real prepared definitions; never a support declaration.
The normal owned/growth preparation is shared, but no CPU battle is executed.
"""
from collections import Counter
from portable_runtime import validate_effect
from effect_spec import describe_effect


def audit_prepared(prepared, stats, body):
    from calculator.buff_manager import BuffManager
    from calculator.timeline import CharState, DEFAULT_ENEMY
    enemy={**DEFAULT_ENEMY,**(prepared.enemy or {})}
    base={c['name']:stats(c) for c in prepared.squad}
    bm=BuffManager(prepared.squad,state=dict(base_stats=base,enemy=enemy,full_burst=False,rng_acc={}))
    name=body['squad'][0];actor=next(c for c in prepared.squad if c['name']==name)
    st=CharState(actor,base[name]['atk'],enemy['code'])
    effects=[]
    for eff,owner in bm._effects:
        if owner!=name:continue
        issue=None
        try:validate_effect(eff,combat={})
        except (ValueError,TypeError) as e:issue=str(e)
        semantic_issue=issue
        if issue is not None:
            diagnostic={k:v for k,v in eff.items() if k not in ('note','polarity','favorite','_source_tag','_quant_group')}
            try:validate_effect(diagnostic,combat={});semantic_issue=None
            except (ValueError,TypeError) as e:semantic_issue=str(e)
        effects.append(dict(name=eff.get('name',''),type=eff.get('type'),stat=eff.get('stat'),
                            family=describe_effect(eff)['family'],timings=eff.get('trigger',{}).get('timing',[]),
                            conditions=eff.get('trigger',{}).get('condition',[]),
                            preflight_passed=issue is None,diagnostic_semantic_issue=semantic_issue,
                            diagnostic_metadata_stripped=True,**(dict(issue=issue) if issue else {})))
    weapon=dict(mode=st.fire_mode,pellets=st.pellets,muzzles=st.muzzles,clip_count=st.clip_count,
                charge_multiplier=st.weapon.get('full_charge_mult',100),spread_start=st.spread_start,
                spread_end=st.spread_end,spread_shots=st._spread_shots_needed)
    from portable_weapon_input import normalize_static_weapon
    from portable_combat import pack_combat
    from portable_runtime import double_words
    from portable_specs import LIMITS as L
    issue=None;normalized=None
    try:
        normalized=normalize_static_weapon(actor,base[name]['atk'],enemy)
        pack_combat([0]*L['INPUT_WORDS'],dict(weapons=[normalized]+[dict(enabled=False) for _ in range(4)],
                    targets=[dict(hp=1e12)]),double_words)
    except (ValueError,TypeError,ZeroDivisionError) as e:issue=str(e)
    gaps=['real_battle_input_adapter_not_connected']
    if issue:gaps.append(issue)
    return dict(character=name,own_effects=len(effects),effects=effects,weapon=weapon,weapon_gaps=gaps,scalar_charge_multiplier_input_available=True,
                normalized_weapon=normalized,weapon_input_preflight_passed=issue is None,weapon_adapter_issue=issue,
                squad_effects=len(bm._effects),all_effects_preflight_passed=all(e['preflight_passed'] for e in effects),
                actual_battle_adapter_connected=False,normal_ui_metal_connected=False,
                cpu_simulation_executed=False,full_character_verified=False)
