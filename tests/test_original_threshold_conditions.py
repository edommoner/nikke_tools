"""Original definitions and bounded trigger receipts share the ordered adapter."""
import copy,hashlib,json,sys,unittest
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

    def test_sealed_count_plateau_inputs_and_cached_source_identity(self):
        from portable_backend import source_hashes
        config=cli.SUITES['original-threshold-conditions'];cached=cli.SUITES['original-threshold-conditions-cache-only']
        self.assertFalse(config['development_only']);self.assertTrue(cached['require_paired_generation'])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        for key in ('script','source','golden','frozen_cases','input_words','output_words'):self.assertEqual(config[key],cached[key])
        _,inputs=cli.prepare_entries(self.adapter,dict(suite='original-threshold-conditions',purpose='sealed',selected_cases=[]))
        raw=(ROOT/config['golden']).read_bytes();golden=json.loads(raw)
        self.assertEqual(hashlib.sha256(inputs).hexdigest(),golden['input_sha256'])
        self.assertEqual(source_hashes(config['source']),golden['source_sha256'])
        prior=json.loads((ROOT/'research/portable-original-support-conditions-v1-expected.json').read_text())
        for key in ('source_sha256','generated_normalized'):self.assertEqual(golden[key],prior[key])
        receipt=json.loads((ROOT/'tests/fixtures/original-threshold-conditions-independent-v1.json').read_text())
        counts=json.loads((ROOT/'tests/fixtures/original-threshold-gpu-counts-v1.json').read_text())
        self.assertEqual(receipt['native_cases'],4);self.assertEqual(receipt['gpu_calls'],0);self.assertFalse(receipt['live_parent_receipt_present'])
        self.assertEqual(counts['package_id'],receipt['package_id'])
        self.assertEqual([[e['activations'] for e in row['effects']] for row in counts['cases']],[[0,0],[1,1],[2,2],[2,2]])
        for key in ('input_sha256','output_sha256'):
            self.assertEqual(counts[key],golden[key]);self.assertEqual(receipt[key],golden[key])
        certificate=json.loads((ROOT/cli.SUITES[cli.compiler_alias('original-threshold-conditions')]['golden']).read_text())
        self.assertEqual(certificate['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(certificate['source_sha256'],golden['source_sha256']);self.assertFalse(certificate['calculation_verified'])

if __name__=='__main__':unittest.main()
