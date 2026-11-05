"""Sampled original effects retain real probability and repeated input contracts."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_original_probability_profiles import profiles
from portable_original_probability_contracts import verify
from world_original_support_native import selected,captures

class OriginalProbabilityConditions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cpu_reference_guard import catalogue_cohort,forbid_execution
        with forbid_execution(),patch('calculator.timeline.simulate',side_effect=AssertionError('Static packing cannot run a battle')):
            cls.config,cls.adapter,cls.rows,cls.data=catalogue_cohort(ROOT,'original-probability-conditions')

    pass

    def test_original_definition_and_probability_are_not_rewritten(self):
        self.assertEqual({r[0] for r in self.rows},set(profiles()))
        for _,words,(case,meta,*_) in self.rows:
            self.assertEqual(len(words),115680);self.assertEqual(len(case['effects']),70)
            self.assertEqual(case['effects'],[r['effect'] for r in case['original_run']['prepared']['effects']])
            self.assertEqual(selected(case),[0]);self.assertTrue(captures(case))
            self.assertEqual(case['effects'][0]['trigger']['condition'],['prob:5'])
            self.assertEqual(sorted(meta['binding_source_indices']),list(range(70)))
            self.assertFalse(case['declared_owner_counter']);self.assertEqual(case['duration'],30)


    def test_altered_chance_and_unknown_scene_cannot_be_certified(self):
        case=copy.deepcopy(self.rows[0][2][0]);case['effects'][0]['trigger']['condition']=['prob:100']
        with self.assertRaisesRegex(AssertionError,'probability must remain'):verify(case,{})
        case['catalogue_profile']['scene_witness']['scenario']='unknown'
        with self.assertRaisesRegex(AssertionError,'Unknown original probability'):verify(case,{})


if __name__=='__main__':unittest.main()
