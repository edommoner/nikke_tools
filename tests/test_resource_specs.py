import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
from resource_specs import consume_resource, minimum_remaining, resource_marker
from resource_limit_cases import CASES


class ResourceSpecsTests(unittest.TestCase):
    def test_resource_marker_is_state_metadata_not_an_arithmetic_operation(self):
        effect=dict(type='buff',stat='gauge_charge_enabled',name='enabled',gauge_id='fuel',target='self')
        self.assertEqual(resource_marker(effect),'fuel')
        for change in ({'type':'instant'},{'gauge_id':''},{'gauge_max':100},{'values':{}},{'target':'all_allies'},{'scaling':'stack_count'}):
            with self.subTest(change=change),self.assertRaises(ValueError):resource_marker({**effect,**change})
        self.assertIsNone(resource_marker(dict(type='instant',stat='gauge_charge')))
    def test_independent_quantities_and_spend_precision(self):
        for name, initial, request, floor, after, spent in CASES:
            with self.subTest(name=name):
                self.assertEqual(consume_resource(initial, request, floor), (after, spent))

    def test_field_scope_and_invalid_quantities(self):
        effect = dict(type='instant', stat='gauge_consume', minimum_remaining=1)
        self.assertEqual(minimum_remaining(effect), 1)
        self.assertEqual(minimum_remaining({}), 0)
        for change in ({'type': 'buff'}, {'stat': 'gauge_charge'}, {'minimum_remaining': True},
                       {'minimum_remaining': -1}, {'minimum_remaining': float('nan')}, {'minimum_remaining': 1e31}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                minimum_remaining(dict(effect, **change))
        with self.assertRaises(ValueError):consume_resource(1, float('inf'))
