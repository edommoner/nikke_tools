"""Actual original positive condition, source identity, and strict GPU negatives."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_reference import digest
from portable_weighted_cover_condition_cases import fixtures
from portable_weighted_cover_condition_contracts import verify
class WeightedCoverCondition(unittest.TestCase):
    def test_saved_actual_original_broken_cover_heals_are_positive(self):
        report=json.loads((ROOT/'tests/fixtures/weighted-cover-condition-cpu-v1.json').read_text());row=report['cases'][0];case=fixtures()[0]
        self.assertTrue(report['passed']);self.assertEqual(row['input_sha256'],digest(case));self.assertEqual(row['native_sha256'],digest(row['native']))
        self.assertEqual(verify(case,row['native']),row['contract']);self.assertEqual(row['contract']['original_definitions'],75)
        self.assertEqual(row['contract']['original_broken_cover_condition_heals'],2);self.assertEqual(row['contract']['positive_hp_heals'],2)
        broken=copy.deepcopy(row['native']);broken['conditional_heals'][0]['cover_hp']=1.
        with self.assertRaises(AssertionError):verify(case,broken)
    def test_positive_contract_sources_match_executed_cpu_receipt(self):
        report=json.loads((ROOT/'tests/fixtures/weighted-cover-condition-cpu-v1.json').read_text())
        for path in ['research/portable_weighted_cover_condition_cases.py','research/world_weighted_cover_condition_native.py','research/portable_weighted_cover_condition_contracts.py','app/weighted_incoming_battle_model.py']:
            self.assertEqual(report['source_sha256'][path],hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()
