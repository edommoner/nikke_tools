import sys
import copy
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from attack_timing_specs import full_burst_landing


class AttackTimingTests(unittest.TestCase):
    def test_compiler_encoding_and_forged_instruction(self):
        import engine_worker
        import detail_gpu as g
        chars = [dict(name=n, _weapon={'burst_stage': '3'}) for n in 'abcde']
        effect = dict(source='slot1', name='landing', type='damage', stat='damage:-2',
                      fixed_value=100, target='target', land_in_full_burst=True,
                      trigger=dict(timing=['burst_cast'], condition=[]))
        literal = g.compile_effects(chars, [(effect, 'a')])
        self.assertEqual(literal['effects'][0][51:53], [2, -2])
        reference = g.compile_effects(chars, [(dict(effect, stat='damage:charge'), 'a')])
        self.assertEqual(reference['effects'][0][52], 4096 + reference['states']['charge'])
        for count in (-257, 257, 4096 + g.NE, .5):
            forged = copy.deepcopy(literal)
            forged['effects'][0][52] = count
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, 'named attack target count'):
                g.run(None, [forged], [[0, 2, 0, 0, -1, 0, 0, 0]], [[0, 0]], [{}])

    def test_count_sources_and_stage(self):
        effect = dict(type='damage', stat='sequential_damage:3', land_in_full_burst=True,
                      trigger=dict(timing=['burst_cast']))
        for suffix, expected in [('3', 3), ('0', 0), ('-2', -2), ('charge', 'charge')]:
            with self.subTest(suffix=suffix):
                self.assertEqual(full_burst_landing(dict(effect, stat='damage:' + suffix), 3).count, expected)
        self.assertEqual(full_burst_landing(dict(effect, stat='damage'), 3).count, 1)
        self.assertIsNone(full_burst_landing(effect, 2))
        self.assertIsNone(full_burst_landing(dict(effect, land_in_full_burst=False), 3))
        self.assertIsNone(full_burst_landing({}, 3))

    def test_reject_ambiguous_or_unimplemented_plans(self):
        effect = dict(type='damage', stat='damage:3', land_in_full_burst=True,
                      trigger=dict(timing=['burst_cast']))
        invalid = [dict(land_in_full_burst=1), dict(type='buff'), dict(stat='dot_damage'),
                   dict(stat='bonus_damage'), dict(stat='accum_split_damage'),
                   dict(stat='damage:'), dict(stat='damage:257'), dict(tick_interval=1),
                   dict(trigger=dict(timing=['every:1s'])), dict(hit_count_gauge_ref='gauge'),
                   dict(stat='damage', scaling='stack_count', scaling_ref='gauge')]
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                full_burst_landing(dict(effect, **changes), 3)


if __name__ == '__main__':
    unittest.main()
