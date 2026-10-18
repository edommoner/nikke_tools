"""Real owned/growth preparation without CPU battle execution.

This stage exposes every real definition and policy. It does not silently
filter unsupported character effects or enable normal-UI GPU acceptance.
"""
import copy
from calculator.buff_manager import BuffManager
from calculator.timeline import DEFAULT_ENEMY, _NIKKE
from portable_weapon_input import normalize_static_weapon


def prepare_static_inputs(prepared, stats):
    enemy={**DEFAULT_ENEMY,**(prepared.enemy or {})}
    base={c['name']:stats(c) for c in prepared.squad}
    bm=BuffManager(prepared.squad,state=dict(base_stats=base,enemy=enemy,full_burst=False,rng_acc={}))
    chars=[{**copy.deepcopy(c),'_weapon':copy.deepcopy(_NIKKE[c['name']])} for c in prepared.squad]
    return dict(chars=chars,effects=[dict(effect=copy.deepcopy(e),owner=n) for e,n in bm._effects],
                base_atk=[base[c['name']]['atk'] for c in chars],
                allies=[dict(base_hp=base[c['name']]['hp'],base_defense=base[c['name']]['def']) for c in chars],
                weapons=[normalize_static_weapon(c,base[c['name']]['atk'],enemy) for c in chars],
                enemy=copy.deepcopy(enemy),policies=dict(config=copy.deepcopy(prepared.config),
                    controls={c['name']:copy.deepcopy(c.get('control',{})) for c in chars},auto=prepared.auto,expected=prepared.expected),
                cpu_battle_executed=False,full_battle_connected=False,all_character_effects_included=True)
