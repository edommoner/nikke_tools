"""Frozen real role witnesses retain the same shared kernel and strict inputs."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli
from portable_original_role_profiles import profiles
from portable_skill_history import SOURCE
spec=importlib.util.spec_from_file_location('sealed_role_catalogue',ROOT/'research/verify-original-catalogue.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogueRolesSealed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from calculator import timeline
        cls.config=cli.SUITES['original-catalogue-roles']
        with cli.forbid_gpu(),patch.object(timeline,'simulate',side_effect=AssertionError('Static regression only')):
            cls.rows,cls.data=cli.prepare_entries(adapter,dict(suite='original-catalogue-roles',purpose='sealed',selected_cases=[]))

    def test_original_parties_and_explicit_controls_are_frozen(self):
        self.assertEqual([r[0] for r in self.rows],list(profiles()))
        self.assertEqual([len(r[2][0]['effects']) for r in self.rows],[90,91,81,81])
        self.assertEqual([bool(r[2][0].get('declared_burst_sequence')) for r in self.rows],[False,False,True,True])
        self.assertTrue(all(r[2][0]['duration']==30 for r in self.rows))

    def test_exact_input_bytes_match_fresh_independently_sealed_baseline(self):
        g=json.loads((ROOT/self.config['golden']).read_text())
        self.assertEqual(hashlib.sha256(self.data).hexdigest(),g['input_sha256'])
        self.assertEqual([r[0] for r in self.rows],[r['name'] for r in g['entries']])
        for i,e in enumerate(g['entries']):
            self.assertEqual(hashlib.sha256(self.data[4+i*115680*4:4+(i+1)*115680*4]).hexdigest(),e['input_sha256'])

    def test_both_backends_share_kernel_golden_and_inputs(self):
        cached=cli.SUITES['original-catalogue-roles-cache-only']
        for k in ('source','script','golden','frozen_cases','inputs','native','input_words','output_words'):self.assertEqual(self.config[k],cached[k])
        self.assertEqual(self.config['source'],SOURCE);self.assertFalse(self.config['development_only'])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1');self.assertTrue(cached['require_paired_generation'])
        from portable_cpu_tests import AUDIT_FILES
        self.assertIn(self.config['golden'],AUDIT_FILES['test_original_catalogue_roles_sealed.py'])

if __name__=='__main__':unittest.main()
