"""Characterize skill-level lookup and observable condition order on CPU only."""
import hashlib
import json
import struct
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ['app', 'scripts', 'tests', 'research']]
from test_target_counter_runtime import manager, NAMES


def effect(conditions):
    return dict(name='probability-value', type='buff', source='스킬2', stat='atk_pct',
                fixed_value=1, target='self', duration=-1,
                trigger=dict(timing=['on_attack'], condition=conditions))


def skill_case(name, values, levels, source, expected, skill_level=None):
    conditions = ['prob:{0}']
    authored = effect(conditions)
    authored.update(trigger_values=values, source=source)
    bm = manager([authored])
    char = bm._char[NAMES[0]]
    char['skill_levels'] = levels
    if skill_level is not None:
        char['skill_level'] = skill_level
    bm.state['rng_expected'] = True
    compiled = bm._effects[0][0]
    observed = []
    accumulators = []
    for i in range(len(expected)):
        observed.append(bm._condition_ok(conditions, NAMES[0], i / 60, compiled))
        accumulators.append(bm.state.get('rng_acc', {}).get(('prob', id(compiled), NAMES[0]), 0))
    assert observed == expected, (name, observed, expected)
    return dict(name=name, trigger_values=values, skill_levels=levels, source=source,
                skill_level=skill_level, passed=observed, accumulators=accumulators)
