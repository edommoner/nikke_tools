"""Sampled original effects retain real probability and repeated input contracts."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli
from portable_original_probability_profiles import profiles
from portable_original_probability_contracts import verify
from world_original_support_native import selected,captures

class OriginalProbabilityConditions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest=dict(suite='original-probability-conditions',purpose='development',selected_cases=[])
        cls.adapter=cli.open_suite(manifest)
        with patch('calculator.timeline.simulate',side_effect=AssertionError('Packing cannot simulate')):
            cls.rows,_=cli.prepare_entries(cls.adapter,manifest)

    def test_original_definition_and_probability_are_not_rewritten(self):
        self.assertEqual({r[0] for r in self.rows},set(profiles()))
        for _,words,(case,meta,*_) in self.rows:
            self.assertEqual(len(words),115680);self.assertEqual(len(case['effects']),70)
            self.assertEqual(case['effects'],[r['effect'] for r in case['original_run']['prepared']['effects']])
            self.assertEqual(selected(case),[0]);self.assertTrue(captures(case))
            self.assertEqual(case['effects'][0]['trigger']['condition'],['prob:5'])
            self.assertEqual(sorted(meta['binding_source_indices']),list(range(70)))
            self.assertFalse(case['declared_owner_counter']);self.assertEqual(case['duration'],30)

    def test_one_repeated_node_preserves_all_hits_and_existing_executor(self):
        config=cli.SUITES['original-probability-conditions'];base=cli.SUITES['original-catalogue-ordered']
        for key in ('script','source','input_words','output_words'):self.assertEqual(config[key],base[key])
        for row in profiles().values():
            self.assertLessEqual(len(row['patterns']),3)
            incoming=[p for p in row['patterns'] if p['id']=='received']
            if row['scene_witness']['scenario']=='control':self.assertFalse(incoming)
            else:self.assertEqual((incoming[0]['spec']['hits'],incoming[0]['spec']['interval']),(64,.04))

    def test_altered_chance_and_unknown_scene_cannot_be_certified(self):
        case=copy.deepcopy(self.rows[0][2][0]);case['effects'][0]['trigger']['condition']=['prob:100']
        with self.assertRaisesRegex(AssertionError,'probability must remain'):verify(case,{})
        case['catalogue_profile']['scene_witness']['scenario']='unknown'
        with self.assertRaisesRegex(AssertionError,'Unknown original probability'):verify(case,{})

if __name__=='__main__':unittest.main()
