"""CPU-only native core/range predicates for the next unadmitted families."""
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / folder) for folder in ['app', 'scripts', 'tests']]
from test_target_counter_runtime import manager, NAMES
from calculator import buff_manager


def effect(conditions):
    return dict(name='geometry-condition', source='스킬1', type='buff', stat='atk_pct',
                fixed_value=1, duration=-1, target='self',
                trigger=dict(timing=['on_attack'], condition=conditions))


def evaluate(conditions, enemy, owner=0, buffs=None, changed_weapon=None):
    bm = manager([effect(conditions)], [owner])
    bm.state['enemy'] = enemy
    bm.state['rng_expected'] = True
    if changed_weapon:
        bm.state['weapon_change'] = {NAMES[owner]: dict(weapon_type=changed_weapon)}
    authored = bm._effects[0][0]
    with patch.object(bm, 'get_buffs', return_value=buffs or {}) as query:
        passed = bm._condition_ok(conditions, NAMES[owner], 0, authored)
    return dict(conditions=conditions, enemy=enemy, owner=owner, roster_weapon=buff_manager._NIKKE[NAMES[owner]]['weapon_type'],
                changed_weapon=changed_weapon, buffs=buffs or {}, passed=passed, stat_queries=query.call_count,
                probability_accumulator=bm.state['rng_acc'].get(('prob', id(authored), NAMES[owner]), 0))
