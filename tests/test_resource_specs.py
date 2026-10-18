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

    def test_compiler_binding_and_forged_instruction(self):
        import engine_worker
        import detail_gpu as g
        names = ['리타', '크라운', '앨리스', '모더니아', 'N102']
        chars = [dict(name=n, _weapon=engine_worker.META[n]) for n in names]
        effect = dict(source='스킬1', name='consume', type='instant', stat='gauge_consume',
                      fixed_value=6, minimum_remaining=1, gauge_id='fuel', target='self',
                      trigger=dict(timing=['battle_start'], condition=[]))
        program = g.compile_effects(chars, [(effect, names[0])])
        self.assertEqual(program['effects'][0][294], 1)
        for value in (-1, 1e31, float('inf')):
            forged = copy.deepcopy(program);forged['effects'][0][294] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                g.run(None, [forged], [[0, 2, 0, 0, -1, 0, 0, 0]], [[0, 0]], [{}])
