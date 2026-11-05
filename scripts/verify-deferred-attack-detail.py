"""Shared cast/landing witnesses; reuse existing squad and legacy comparators."""
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
from detail_coverage import a, body_for
from calculator.buff_manager import BuffManager
import detail_gpu as g


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


p = load('deferred_periodic', 'scripts/verify-periodic-detail.py')
legacy = load('deferred_legacy', 'scripts/verify-named-target-detail.py')
primitive = load('deferred_primitive', 'scripts/verify-detail.py')
E = p.effect




def scenarios():
    for name, stat, enabled, owner, expected in (
        ('literal-parent-and-children', 'sequential_damage:3', True, 2, 3),
        ('latched-reference-and-gate', 'sequential_damage:cast count', True, 2, 1),
        ('zero-count', 'sequential_damage:0', True, 2, 0),
        ('negative-count', 'sequential_damage:-2', True, 2, 0),
        ('missing-reference', 'sequential_damage:absent', True, 2, 0),
        ('disabled-landing', 'sequential_damage:3', False, 2, 3),
        ('stage-two-is-immediate', 'sequential_damage:3', True, 1, 3),
        ('legacy-and-delayed-coexist', 'sequential_damage:3', True, 2, 3),
        ('query-scope-additive', 'sequential_damage:3', True, 2, 3),
        ('query-scope-replacement', 'sequential_damage:3', True, 2, 3),
    ):
        count = E('cast count', 'buff', '', 0, max_stack=9)
        count['trigger']['timing'] = ['battle_start', 'full_burst_start']
        effects = [count, E('cast gate', 'buff', '', 0),
                   E('earlier ATK', 'buff', 'atk_pct', 10, event='burst_cast', duration=10),
                   E('landing', 'damage', stat, 100, 'target', event='burst_cast',
                     land_in_full_burst=enabled, condition=['self_state:cast gate'], max_trigger=1),
                   E('consume gate', 'instant', 'remove_named_buff', 0, event='burst_cast', target_effect='cast gate'),
                   E('later ATK', 'buff', 'atk_pct', 200, event='burst_cast', duration=10),
                   E('entry ATK', 'buff', 'atk_pct', 100, event='full_burst_start', duration=10),
                   E('child attack', 'damage', 'damage', 100, 'target', event='hit_count:landing:1'),
                   E('child changes ATK', 'buff', 'atk_pct', 20, event='hit_count:landing:1', max_stack=20)]
        if name == 'legacy-and-delayed-coexist':
            effects.insert(4, E('legacy bonus', 'damage', 'bonus_damage', 50, 'target', event='burst_cast'))
        if name.startswith('query-scope-'):
            attack = next(e for e in effects if e['name'] == 'landing')
            attack.update(scaling='max_hp_additive' if name.endswith('additive') else 'max_hp_replacement', scaling_hp_pct=10)
            index = effects.index(attack)
            effects[index:index] = [E('earlier HP', 'buff', 'max_hp_only_pct', 50, event='burst_cast', duration=10),
                                    E('earlier magnitude', 'buff', 'dmg_scale_mag_pct', 50, event='burst_cast', duration=10, target_effect='landing')]
            effects[index + 3:index + 3] = [E('later HP', 'buff', 'max_hp_only_pct', 100, event='burst_cast', duration=10),
                                           E('later magnitude', 'buff', 'dmg_scale_mag_pct', 100, event='burst_cast', duration=10, target_effect='landing'),
                                           E('child magnitude', 'buff', 'dmg_scale_mag_pct', 100, event='burst_cast', duration=10, target_effect='child attack')]
        yield name, owner, effects, expected, enabled and owner == 2






if __name__ == '__main__':
    main()
