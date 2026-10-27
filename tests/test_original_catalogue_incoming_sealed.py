"""Frozen incoming witnesses reuse one common calculation and independent golden."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli
from portable_original_incoming_profiles import profiles
spec=importlib.util.spec_from_file_location('sealed_incoming_catalogue',ROOT/'research/verify-original-catalogue.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogueIncomingSealed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from calculator import timeline
        cls.config=cli.SUITES['original-catalogue-incoming']
        with cli.forbid_gpu(),patch.object(timeline,'simulate',side_effect=AssertionError('Static regression only')):
            cls.rows,cls.data=cli.prepare_entries(adapter,dict(suite='original-catalogue-incoming',purpose='sealed',selected_cases=[]))

    def test_original_parties_definitions_and_real_attack_inputs_are_frozen(self):
        self.assertEqual([r[0] for r in self.rows],list(profiles()))
        self.assertEqual([len(r[2][0]['effects']) for r in self.rows],[81,81,74,74])
        self.assertEqual([bool(r[2][0].get('declared_burst_sequence')) for r in self.rows],[True,False,False,False])
        for name,words,(case,meta,b,d) in self.rows:
            self.assertEqual(case['duration'],30);self.assertEqual(sum(p['kind']=='attack' for p in case['patterns']),3)
            self.assertFalse(case['declared_owner_counter'])

    def test_exact_input_bytes_match_independent_sealed_baseline(self):
        g=json.loads((ROOT/self.config['golden']).read_text())
        self.assertEqual(hashlib.sha256(self.data).hexdigest(),g['input_sha256'])
        self.assertEqual([r[0] for r in self.rows],[r['name'] for r in g['entries']])
        for i,e in enumerate(g['entries']):self.assertEqual(hashlib.sha256(self.data[4+i*115680*4:4+(i+1)*115680*4]).hexdigest(),e['input_sha256'])

    def test_cuda_and_metal_share_executor_inputs_golden_and_dependencies(self):
        cached=cli.SUITES['original-catalogue-incoming-cache-only']
        for k in ('source','script','golden','frozen_cases','inputs','native','input_words','output_words'):self.assertEqual(self.config[k],cached[k])
        self.assertFalse(self.config['development_only']);self.assertTrue(cached['require_paired_generation'])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        from portable_cpu_tests import AUDIT_FILES
        self.assertIn(self.config['golden'],AUDIT_FILES['test_original_catalogue_incoming_sealed.py'])

if __name__=='__main__':unittest.main()
