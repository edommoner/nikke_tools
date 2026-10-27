"""Frozen original burst compositions share one implementation and cache key."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli,engine_worker
spec=importlib.util.spec_from_file_location('catalogue_burst_tests',ROOT/'research/verify-original-catalogue.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogueBurst(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from calculator import timeline
        cls.config=cli.SUITES['original-catalogue-burst']
        with cli.forbid_gpu(),patch.object(timeline,'simulate',side_effect=AssertionError('Static regression must not run a battle')):
            cls.rows,cls.data=cli.prepare_entries(adapter,dict(suite='original-catalogue-burst',purpose='sealed',selected_cases=[]))

    def test_all_four_original_30s_rosters_and_definitions_are_preserved(self):
        self.assertEqual([r[2][0]['names'][0] for r in self.rows],['라피 : 레드 후드','홍련 : 흑영','레드 후드','신데렐라'])
        self.assertEqual([len(r[2][0]['effects']) for r in self.rows],[87,76,81,74])
        for name,words,(case,meta,bindings,descriptor) in self.rows:
            with self.subTest(name=name):
                original=case['original_run']['prepared']
                self.assertEqual(case['duration'],30);self.assertEqual(len(words),115680)
                self.assertEqual(case['effects'],[r['effect'] for r in original['effects']])
                self.assertEqual(case['owners'],[case['names'].index(r['owner']) for r in original['effects']])
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(case['effects']))))
                self.assertFalse(case['declared_owner_counter'])
                self.assertTrue(all(b['kind']==3 and b['owner']==[0,0,1] for b in case['typed_bindings']))

    def test_exact_inputs_match_the_independent_golden_without_cpu_or_gpu(self):
        golden=json.loads((ROOT/self.config['golden']).read_text())
        self.assertEqual(hashlib.sha256(self.data).hexdigest(),golden['input_sha256'])
        self.assertEqual([r[0] for r in self.rows],[r['name'] for r in golden['entries']])
        for i,entry in enumerate(golden['entries']):
            raw=self.data[4+i*115680*4:4+(i+1)*115680*4]
            self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['input_sha256'])

    def test_same_gpu_kernel_and_expected_outputs_drive_both_backends(self):
        cached=cli.SUITES['original-catalogue-burst-cache-only']
        for key in ('source','script','golden','frozen_cases','inputs','native','input_words','output_words'):self.assertEqual(self.config[key],cached[key])
        self.assertFalse(self.config['development_only']);self.assertTrue(cached['require_paired_generation'])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        current=json.loads((ROOT/self.config['golden']).read_text());prior=json.loads((ROOT/cli.SUITES['original-catalogue-initial']['golden']).read_text())
        self.assertEqual(current['source_sha256'],prior['source_sha256'])
        self.assertEqual(current['generated_normalized'],prior['generated_normalized'])

    def test_comparison_golden_is_a_required_package_and_cpu_audit_dependency(self):
        from portable_cpu_tests import AUDIT_FILES,validate_dependency_files
        prior=cli.SUITES['original-catalogue-initial']['golden']
        self.assertIn(prior,self.config['support_files'])
        self.assertIn(prior,AUDIT_FILES['test_original_catalogue_burst.py'])
        with self.assertRaisesRegex(ValueError,'missing from immutable payload'):
            validate_dependency_files(ROOT,['test_original_catalogue_burst.py'],included=[])

if __name__=='__main__':unittest.main()
