"""Native clock semantics, canonical encoding and private API boundaries."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_skill_cooldown_cases import fixtures,negative_inputs
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L,FIELDS as F
from world_projectile_native import observe


class SkillCooldownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('skill_clock_adapter',ROOT/'research/verify-world-skill-cooldown-short.py')
        cls.adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.adapter)
        cls.rows=fixtures();cls.native=[observe(c) for c in cls.rows]

    def test_percentage_adjusts_remaining_time_and_clamps_at_zero(self):
        traces=[pair[1] for pair in self.native]
        self.assertLess(traces[1][0]['created'],traces[0][0]['created'])
        self.assertGreater(traces[4][0]['created'],traces[0][0]['created'])
        self.assertEqual(traces[2],traces[3])
        self.assertEqual(traces[2],traces[17])
        self.assertEqual(traces[18],[])
        self.assertEqual(traces[19],[])
        self.assertGreater(len(traces[20]),0)
        self.assertGreater(traces[20][0]['created'],.5)

    def test_one_shot_reverts_to_original_period_without_rescaling_it(self):
        times=[event['created'] for event in self.native[14][1]]
        self.assertLess(times[0],.4)
        self.assertGreaterEqual(len(times),3)
        for a,b in zip(times,times[1:]):self.assertAlmostEqual(b-a,.4,places=12)

    def test_uninitialized_and_absent_clocks_are_not_created(self):
        self.assertEqual(self.native[0][1],self.native[5][1])
        self.assertEqual(self.native[0][1],self.native[11][1])
        self.assertEqual(self.native[12][1],[])

    def test_compound_targets_are_a_set_and_target_effect_is_ignored(self):
        self.assertEqual(self.native[1][1],self.native[7][1])
        self.assertEqual(self.native[1][1],self.native[13][1])
        first={row:next(e['created'] for e in self.native[10][1] if e['row']==row) for row in (0,1)}
        self.assertLess(first[1],first[0])
        self.assertNotEqual(self.native[15][1],self.native[16][1])

    def test_private_input_and_canonical_kind_are_preserved(self):
        before=copy.deepcopy(self.rows)
        for case in self.rows:
            words,_,_=self.adapter.suite.compile_case(case)
            for index,effect in enumerate(case['effects']):
                if effect.get('stat')!='skill_cooldown_reduce_pct':continue
                self.assertEqual(words[L['DEFINITION_BASE']+index*L['DEFINITION_WORDS']+F['KIND']],22)
                for options in ({},dict(combat={})):
                    with self.assertRaises(UnsupportedPortable):validate_effect(effect,**options)
                validate_effect(effect,combat={},world_frame=True)
        self.assertEqual(self.rows,before)
        self.assertEqual(len(negative_inputs(self.adapter.suite.compile_case)),4)


if __name__=='__main__':unittest.main()
