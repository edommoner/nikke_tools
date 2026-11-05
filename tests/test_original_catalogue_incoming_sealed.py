"""Frozen incoming witnesses reuse one common calculation and independent golden."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_original_incoming_profiles import profiles
spec=importlib.util.spec_from_file_location('sealed_incoming_catalogue',ROOT/'research/verify-original-catalogue.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogueIncomingSealed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cpu_reference_guard import catalogue_cohort,forbid_execution
        with forbid_execution(),patch('calculator.timeline.simulate',side_effect=AssertionError('Static packing cannot run a battle')):
            cls.config,cls.adapter,cls.rows,cls.data=catalogue_cohort(ROOT,'original-catalogue-incoming',adapter)

    pass

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


if __name__=='__main__':unittest.main()
