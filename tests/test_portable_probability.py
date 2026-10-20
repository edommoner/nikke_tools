import copy
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
import engine_worker
from timer_registry_cases import NAMES
from portable_runtime import compile_program, UnsupportedPortable
from portable_specs import LIMITS as L, FIELDS as F, ABI, check_schema


class ProbabilityInput(unittest.TestCase):
    def compile(self, conditions, values=None, level=3):
        chars = [dict(name=n, skill_levels={'1': level, '2': 10, '3': 10}, _weapon=dict(engine_worker.META[n])) for n in NAMES]
        effect = dict(name='phase', type='buff', source='스킬1', stat='atk_pct', fixed_value=1,
                      target='self', duration=-1, trigger=dict(timing=['on_attack'], condition=conditions))
        if values is not None:
            effect['trigger_values'] = values
        original = copy.deepcopy(effect)
        result = compile_program(chars, [(effect, NAMES[0])], [[0, 0, 7, 0, 0, -1, 0, 0]], [1000] * 5)
        self.assertEqual(effect, original)
        return result

    def test_existing_strides_and_explicit_output_tail(self):
        check_schema()
        self.assertEqual(ABI, 0x50455670)
        self.assertEqual((L['INPUT_WORDS'], L['OUTPUT_WORDS']), (86016, 159744))
        self.assertEqual(L['PROBABILITY_STATE_BASE'], L['RECIPIENT_ORDER_BASE'] + L['CARRIERS'] * 2)
        self.assertEqual(L['OUTPUT_WORDS'] - L['PROBABILITY_STATE_BASE'] - L['PROBABILITY_STATE_WORDS'], 512)

    def test_native_skill_value_and_fallback_with_authored_order(self):
        import struct
        for values, expected in [({'3': 50, '10': 100}, .5), ({'10': 20}, .2)]:
            words, metadata = self.compile(['self_stat_above:atk_pct:1', 'prob:{0}'], values)
            base = L['CONDITION_BASE']
            self.assertEqual([words[base], words[base + 4]], [8, 26])
            self.assertEqual(words[base + 6:base + 8], list(struct.unpack('<II', struct.pack('<d', expected))))
            self.assertEqual(metadata['probability_definitions'], [0])

    def test_empty_skill_values_remains_false_without_probability_op(self):
        words, _ = self.compile(['prob:{0}'], {})
        base = L['CONDITION_BASE']
        self.assertEqual(words[base:base + 4], [25, 0, 0, 0])

    def test_percentage_boundaries_and_scientific_notation(self):
        for value in ['0', '-0', '.5', '1e-3', '100']:
            with self.subTest(value=value):
                self.compile(['prob:' + value])

    def test_rejects_invalid_probabilities_before_gpu_submission(self):
        for value in ['-1', '100.0001', 'nan', 'inf', '1e309', '{1}', '', ' 20 ', 'twenty']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.compile(['prob:' + value])
        for values in [{'3': True}, {'3': math.nan}, {'3': None}, {'3': 101}, {'3': -1}, []]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.compile(['prob:{0}'], values)

    def test_noncanonical_period_does_not_silently_change_native_phase(self):
        from portable_trigger_specs import validate_input
        with self.assertRaisesRegex(ValueError, 'seconds suffix'):
            validate_input(dict(trigger=dict(timing=['every:0.1'], condition=['prob:20'])))


if __name__ == '__main__':
    unittest.main()
