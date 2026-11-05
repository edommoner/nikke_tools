"""Saved actual original battles bind identity, strict receipts and scope."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from historical_engine_reference import source_preimage
from portable_weighted_battle_cases import fixtures
from portable_weighted_battle_contracts import verify

class WeightedBattleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'tests/fixtures/weighted-battle-cpu-v1.json').read_text());cls.cases=fixtures()
    def test_calculation_sources_remain_those_used_by_saved_native_runs(self):
        for path in ['app/weighted_incoming_battle_model.py','app/incoming_weighted_allocation.py','research/world_weighted_battle_native.py','research/portable_weighted_battle_cases.py','research/portable_weighted_battle_contracts.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']:
            self.assertEqual(self.report['source_sha256'][path],hashlib.sha256(source_preimage(ROOT,path)).hexdigest(),path)
    def test_corrupt_body_share_cover_hp_or_original_identity_is_rejected(self):
        case=self.cases[0];row=self.report['cases'][0]
        for field in ('share','cover','identity'):
            native=copy.deepcopy(row['native'])
            if field=='share':native['weighted_incoming']['snapshots'][0]['shares'][0]+=1.
            elif field=='cover':native['weighted_incoming']['cover_receipts'][0]['hp_after']+=1.
            else:native['original_input_identity']['definitions']-=1
            with self.assertRaises(AssertionError):verify(case,native)

if __name__=='__main__':unittest.main()
