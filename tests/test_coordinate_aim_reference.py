"""Aim contracts before runtime wiring: native order, passive hooks and static IR."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'research')]
import engine_worker
from calculator import timeline
from portable_coordinate_aim_cases import fixtures
from portable_coordinate_aim_contracts import verify
from portable_coordinate_aim_specs import compile_aim, WINDOWS, ANCHORS
from portable_coordinate_scene_specs import compile_scene
from world_coordinate_aim_native import observe
from world_coordinate_physical_common import observe as base_observe
from world_coordinate_matrix_common import common_policy
from world_frame_native import roster_names


def descriptors(case):
    return compile_scene(dict(patterns=case['patterns'], commands=[('capture', 0., 0, 0)]), allow_core=True)[1]


class AimReferenceTests(unittest.TestCase):
    def test_all_native_lifetimes_windows_anchors_and_arbitration_contracts(self):
        cases = fixtures()
        self.assertEqual(len(cases), 30)
        for case in cases:
            native, _ = observe(case)
            contract = verify(case, native)
            self.assertTrue(contract['verified'], case['name'])
            self.assertFalse(contract['gpu_supported'])

    def test_observation_is_transparent_and_restores_every_hook(self):
        case = fixtures()[6]
        hooks = {k: getattr(timeline.CharState, k) for k in ('tick', '_wants_control', '_when_open', '_anchor_at', '_aim_point')}
        profiler = sys.getprofile()
        with common_policy():
            expected = base_observe(case)
        observed, trace = observe(case)
        observed.pop('coordinate_aim')
        expected_trace = expected.pop('skill_trace')
        self.assertEqual(observed, expected)
        self.assertEqual(trace, expected_trace)
        self.assertIs(sys.getprofile(), profiler)
        for name, hook in hooks.items():
            self.assertIs(getattr(timeline.CharState, name), hook)
        with patch('world_coordinate_aim_native.physical', side_effect=RuntimeError('observer failure')):
            with self.assertRaisesRegex(RuntimeError, 'observer failure'):
                observe(case)
        for name, hook in hooks.items():
            self.assertIs(getattr(timeline.CharState, name), hook)

    def test_static_ir_preserves_every_native_clock_without_executing_it(self):
        windows, anchors = set(), set()
        for case in fixtures():
            before = copy.deepcopy(case)
            desc = descriptors(case)
            with patch.object(timeline, 'simulate', side_effect=AssertionError('battle')), \
                 patch.object(timeline, '_arbitrate_control', side_effect=AssertionError('arbitration')), \
                 patch.object(timeline.CharState, '_when_open', side_effect=AssertionError('window')):
                ir = compile_aim(case, desc, names=roster_names(case))
            self.assertEqual(case, before)
            self.assertFalse(ir['gpu_execution_connected'])
            for owner in ir['owners']:
                for row in owner['entries']:
                    when = row['when']
                    (windows if when['kind'] == 0 else anchors).add(when['code'])
        self.assertEqual(windows, set(range(len(WINDOWS))))
        self.assertEqual(anchors, set(range(len(ANCHORS))))

    def test_ir_priorities_and_reserved_target_are_explicit(self):
        case = fixtures()[0]
        case['controls'][0]['priority'] = 'high'
        ir = compile_aim(case, descriptors(case), names=roster_names(case))
        self.assertEqual(ir['owners'][0]['entries'][0]['priority'], 30)
        case['controls'][0]['aim'][0].update(at='core', priority='low')
        ir = compile_aim(case, descriptors(case), names=roster_names(case))
        row = ir['owners'][0]['entries'][0]
        self.assertEqual((row['priority'], row['target_kind'], row['target_slot']), (10, 0, 0))

    def test_ir_rejects_unknown_target_nonfinite_span_and_capacity(self):
        for edit in ('target', 'nonfinite', 'capacity', 'priority', 'unknown-key'):
            case = fixtures()[0]
            row = case['controls'][0]['aim'][0]
            if edit == 'target':
                row['at'] = 'missing'
            elif edit == 'nonfinite':
                row.update(anchor='combat_start', offset=float('nan'), len=.1)
            elif edit == 'capacity':
                case['controls'][0]['aim'] *= 9
            elif edit == 'priority':
                row['priority'] = -1
            else:
                row['unknown'] = True
            with self.assertRaises(ValueError, msg=edit):
                compile_aim(case, descriptors(case), names=roster_names(case))

    def test_native_strict_conflict_is_not_silently_serialized(self):
        case = fixtures()[5]
        case['control_mode'] = 'strict'
        with self.assertRaises(ValueError):
            observe(case)

    def test_ir_rejects_ambiguous_labels_body_aliases_and_disabled_coordinates(self):
        case = fixtures()[0]
        original = descriptors(case)
        for edit in ('duplicate-label', 'reserved-core', 'body-slot', 'duplicate-slot', 'disabled'):
            desc = copy.deepcopy(original)
            current = copy.deepcopy(case)
            if edit == 'duplicate-label':
                desc['rows'][1]['label'] = desc['rows'][0]['label']
            elif edit == 'reserved-core':
                desc['rows'][0]['label'] = 'core'
            elif edit == 'body-slot':
                desc['rows'][0]['slot'] = 0
            elif edit == 'duplicate-slot':
                desc['rows'][1]['slot'] = desc['rows'][0]['slot']
            else:
                current['enemy'].pop('coord')
            with self.assertRaises(ValueError, msg=edit):
                compile_aim(current, desc, names=roster_names(current))


if __name__ == '__main__':
    unittest.main()
