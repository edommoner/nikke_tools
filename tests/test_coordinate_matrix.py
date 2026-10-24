"""Common input policy, historical isolation and actual area/physical battle caller."""
import copy
import importlib.util
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'research')]
import engine_worker
from calculator import aim, timeline
import portable_coordinate_area_specs as legacy
import portable_coordinate_numeric_v1 as numeric
from portable_coordinate_matrix_specs import coefficients, compiler_policy, PROFILE
from world_coordinate_matrix_common import common_policy, distance
s = importlib.util.spec_from_file_location('matrix_adapter_test', ROOT/'research/verify-coordinate-matrix-short.py')
a = importlib.util.module_from_spec(s)
s.loader.exec_module(a)


class MatrixTests(unittest.TestCase):
    def test_pack_has_no_host_transcendental_battle_or_geometry_oracle(self):
        with patch.object(math, 'sin', side_effect=AssertionError('host sin')), \
             patch.object(math, 'cos', side_effect=AssertionError('host cos')), \
             patch.object(math, 'radians', side_effect=AssertionError('host radians')), \
             patch.object(timeline, 'simulate', side_effect=AssertionError('battle')), \
             patch.object(aim.Shape, 'dist', side_effect=AssertionError('distance')), \
             patch.object(a, 'native_reference', side_effect=AssertionError('native')):
            rows, raw = a.prepare()
        self.assertEqual((len(rows), sum(d is not None for _, _, d in rows)), (151, 136))
        self.assertEqual(len(raw), 4 + 151*a.INPUT_WORDS*4)

    def test_only_matrix_fields_change_and_cases_are_immutable(self):
        case = a.fixtures()[4]
        before = copy.deepcopy(case)
        old, *_ = a.parent.compile_case(case)
        new, _, _, desc = a.compile_case(case)
        allowed = set()
        for row in desc['rows']:
            at = 107592 + legacy.LAYOUT['HEADER'] + row['slot']*8 + 2
            allowed.update(range(at, at+4))
            co, si = coefficients(row['shape'])
            from portable_coordinate_scene_specs import bits
            self.assertEqual(new[at:at+4], bits(co)+bits(si))
        self.assertEqual(case, before)
        self.assertTrue(any(x != y for x, y in zip(old, new)))
        self.assertTrue(all(x == y or i in allowed for i, (x, y) in enumerate(zip(old, new))))

    def test_axes_signed_zero_and_independent_known_values(self):
        self.assertEqual(coefficients(aim.Shape(0, 0, w=2, h=2, rot=90.)), (0., 1.))
        co, si = coefficients(aim.Shape(0, 0, w=2, h=2, rot=-0.))
        self.assertEqual((numeric.bits(co), numeric.bits(si)), (numeric.ONE, numeric.SIGN))
        self.assertEqual(distance(aim.Shape(0, 0, w=2, h=4, rot=90.), 3., 0.), 1.)
        self.assertEqual(distance(aim.Shape(0, 0, r=2.), 3., 4.), 3.)
        with self.assertRaises(ValueError):
            coefficients(aim.Shape(0, 0, w=2, h=4, rot=float('inf')))

    def test_hooks_restore_after_exception_and_historical_profile_is_retained(self):
        original_dist, original_coeff = aim.Shape.dist, legacy.rotation_coefficients
        with self.assertRaisesRegex(RuntimeError, 'witness'):
            with compiler_policy(), common_policy():
                self.assertIs(aim.Shape.dist, distance)
                self.assertIs(legacy.rotation_coefficients, coefficients)
                raise RuntimeError('witness')
        self.assertIs(aim.Shape.dist, original_dist)
        self.assertIs(legacy.rotation_coefficients, original_coeff)
        shape = aim.Shape(0, 0, w=2, h=2, rot=90.)
        self.assertNotEqual(legacy.rotation_coefficients(shape), coefficients(shape))

    def test_touch_neighbor_changes_real_selection_under_explicit_policy(self):
        edge = 11. + 1e-9
        inside = aim.Shape(math.nextafter(edge, -math.inf), 40., w=100., h=2., rot=90.)
        outside = aim.Shape(math.nextafter(edge, math.inf), 40., w=100., h=2., rot=90.)
        self.assertTrue(outside.contains(0., 0., 10.))
        with common_policy():
            self.assertTrue(inside.contains(0., 0., 10.))
            self.assertFalse(outside.contains(0., 0., 10.))

    def test_all_new_worlds_reach_real_skill_and_physical_packet_producers(self):
        for case in a.fixtures():
            _, meta, bindings, desc = a.compile_case(case)
            observed = a.native_reference((case, meta, bindings, desc))
            self.assertEqual(observed['area_matrix_policy'], PROFILE)
            self.assertEqual(observed['reference_kind'], 'deterministic-common-cpu')
            self.assertTrue(observed['physical_pellets'])
            self.assertTrue(observed['skill_trace'])
            self.assertTrue(observed['geometry_cache']['queries'])
            if case['name'].endswith('common-matrix-touch-True'):
                historical = a.parent.native_reference((case, meta, bindings, desc))
                self.assertEqual([e['amount'] for e in historical['skill_trace']], [2000, 3000])
                self.assertEqual([e['amount'] for e in observed['skill_trace']], [2000])
            if case['name'].endswith('common-matrix-touch-False'):
                self.assertEqual([e['amount'] for e in observed['skill_trace']], [2000, 3000])


if __name__ == '__main__':
    unittest.main()
