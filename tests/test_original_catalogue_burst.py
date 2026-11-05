import engine_worker
"""Frozen original burst compositions share one implementation and cache key."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('catalogue_burst_tests',ROOT/'research/verify-original-catalogue.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogueBurst(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cpu_reference_guard import catalogue_cohort,forbid_execution
        with forbid_execution(),patch('calculator.timeline.simulate',side_effect=AssertionError('Static packing cannot run a battle')):
            cls.config,cls.adapter,cls.rows,cls.data=catalogue_cohort(ROOT,'original-catalogue-burst',adapter)

    pass

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



if __name__=='__main__':unittest.main()
