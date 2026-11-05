"""Actual original positive condition, source identity, and strict GPU negatives."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_weighted_cover_condition_cases import fixtures
from portable_weighted_cover_condition_contracts import verify
class WeightedCoverCondition(unittest.TestCase):
    def test_positive_contract_sources_match_executed_cpu_receipt(self):
        report=json.loads((ROOT/'tests/fixtures/weighted-cover-condition-cpu-v1.json').read_text())
        for path in ['research/portable_weighted_cover_condition_cases.py','research/world_weighted_cover_condition_native.py','research/portable_weighted_cover_condition_contracts.py','app/weighted_incoming_battle_model.py']:
            self.assertEqual(report['source_sha256'][path],hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()
