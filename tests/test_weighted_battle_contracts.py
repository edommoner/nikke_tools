"""Saved actual original battles bind identity, strict receipts and scope."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_weighted_battle_cases import fixtures
from portable_weighted_battle_contracts import verify
from portable_reference import digest,REFERENCES
from portable_readiness_semantics import reference_readiness

class WeightedBattleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'tests/fixtures/weighted-battle-cpu-v1.json').read_text());cls.cases=fixtures()
    def test_all_original_stages_and_saved_full_native_contracts_are_bound(self):
        saved=self.report['cases'];self.assertEqual(len(saved),7);self.assertEqual(len(self.cases),7)
        self.assertTrue(self.report['passed']);self.assertEqual(self.report['gpu_calls'],dict(build=0,execute=0))
        for case,row in zip(self.cases,saved,strict=True):
            self.assertEqual(row['name'],case['name']);self.assertEqual(row['input_sha256'],digest(case))
            self.assertEqual(row['native_sha256'],digest(row['native']));self.assertEqual(verify(case,row['native']),row['contract'])
        self.assertEqual([c['contract']['favorite_stage'] for c in self.cases[:4]],[0,1,2,3])
        self.assertEqual([r['contract']['original_definitions'] for r in saved[:4]],[69,74,75,76])
    def test_calculation_sources_remain_those_used_by_saved_native_runs(self):
        for path in ['app/weighted_incoming_battle_model.py','app/incoming_weighted_allocation.py','research/world_weighted_battle_native.py','research/portable_weighted_battle_cases.py','research/portable_weighted_battle_contracts.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']:
            self.assertEqual(self.report['source_sha256'][path],hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
    def test_corrupt_body_share_cover_hp_or_original_identity_is_rejected(self):
        case=self.cases[0];row=self.report['cases'][0]
        for field in ('share','cover','identity'):
            native=copy.deepcopy(row['native'])
            if field=='share':native['weighted_incoming']['snapshots'][0]['shares'][0]+=1.
            elif field=='cover':native['weighted_incoming']['cover_receipts'][0]['hp_after']+=1.
            else:native['original_input_identity']['definitions']-=1
            with self.assertRaises(AssertionError):verify(case,native)
    def test_reference_route_and_scope_cannot_be_promoted_to_metal_or_default(self):
        self.assertEqual(REFERENCES['weighted-incoming-common'][0],'portable_weighted_battle_cases')
        for target in ('all_allies','self_cover'):
            r=reference_readiness(dict(phase='effect',kind='buff',stat='received_dmg_split',target=target));cpu=r['declared_weighted_battle_cpu']
            self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported'])
            self.assertEqual(cpu['evidence_sha256'],hashlib.sha256((ROOT/cpu['evidence']).read_bytes()).hexdigest())
            self.assertTrue(cpu['original_carrier_lifetime_connected']);self.assertTrue(cpu['independent_cover_recipient'])
            for key in ('metal_battle_verified','cuda_battle_verified','in_game_rules_verified'):self.assertFalse(cpu[key])

if __name__=='__main__':unittest.main()
