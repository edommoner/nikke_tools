"""Original definitions and bounded trigger receipts share the ordered adapter."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli
from portable_original_threshold_profiles import profiles
from portable_original_threshold_contracts import verify
from world_original_support_native import selected,captures

class OriginalThresholdConditions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest=dict(suite='original-threshold-conditions',purpose='development',selected_cases=[])
        cls.adapter=cli.open_suite(manifest)
        with patch('calculator.timeline.simulate',side_effect=AssertionError('Packing cannot simulate')):
            cls.rows,_=cli.prepare_entries(cls.adapter,manifest)

    def test_original_roster_definitions_and_binding_identity(self):
        self.assertEqual(set(profiles()),{r[0] for r in self.rows})
        for _,words,(case,meta,*_) in self.rows:
            self.assertEqual(len(words),115680);self.assertEqual(len(case['effects']),72)
            self.assertEqual(case['names'],['비스킷','미란다','노아','센티','드레이크'])
            self.assertEqual(case['effects'],[r['effect'] for r in case['original_run']['prepared']['effects']])
            self.assertEqual(sorted(meta['binding_source_indices']),list(range(72)))
            self.assertEqual(selected(case),[2,3]);self.assertTrue(captures(case));self.assertTrue(meta['ordered_recipients'])
            self.assertFalse(case['declared_owner_counter']);self.assertEqual(case['duration'],30)

    def test_same_existing_executor_and_distinct_literal_controls(self):
        config=cli.SUITES['original-threshold-conditions'];base=cli.SUITES['original-catalogue-ordered']
        for key in ('script','source','input_words','output_words'):self.assertEqual(config[key],base[key])
        self.assertEqual([len(r['patterns'])-1 for r in profiles().values()],[0,2,4,6])
        for row in profiles().values():
            self.assertNotIn('declared_burst_sequence',row);self.assertNotIn('declared_manual_sequences',row)

    def test_handler_attempts_cannot_substitute_for_successful_activations(self):
        case=next(r[2][0] for r in self.rows if '-exhausted/' in r[0])
        fake=dict(support_conditions=dict(activations=[dict(row=row,owner=0,time=t) for row in (2,3) for t in (1.,7.,14.)],attempts=[]))
        with self.assertRaisesRegex(AssertionError,'successful original activations'):verify(case,fake)
        bad=copy.deepcopy(case);bad['catalogue_profile']['scene_witness']['scenario']='unknown'
        with self.assertRaisesRegex(AssertionError,'Unknown original threshold'):verify(bad,fake)

if __name__=='__main__':unittest.main()
