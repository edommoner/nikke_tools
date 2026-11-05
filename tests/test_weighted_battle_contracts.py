"""Saved actual original battles bind identity, strict receipts and scope."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_weighted_battle_cases import fixtures
from portable_weighted_battle_contracts import verify

class WeightedBattleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'tests/fixtures/weighted-battle-cpu-v1.json').read_text());cls.cases=fixtures()
    def test_corrupt_body_share_cover_hp_or_original_identity_is_rejected(self):
        case=self.cases[0];row=self.report['cases'][0]
        for field in ('share','cover','identity'):
            native=copy.deepcopy(row['native'])
            if field=='share':native['weighted_incoming']['snapshots'][0]['shares'][0]+=1.
            elif field=='cover':native['weighted_incoming']['cover_receipts'][0]['hp_after']+=1.
            else:native['original_input_identity']['definitions']-=1
            with self.assertRaises(AssertionError):verify(case,native)

if __name__=='__main__':unittest.main()
