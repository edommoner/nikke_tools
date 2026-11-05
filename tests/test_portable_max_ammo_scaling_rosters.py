"""Original Emilia native observations remain transparent and unmodified."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_max_ammo_scaling_roster_cases import fixtures
from world_max_ammo_scaling_roster_native import observe,bare
from portable_max_ammo_scaling_roster_contracts import verify
class MaxAmmoRosterTests(unittest.TestCase):
    def test_original_profiles_contract_and_transparency(self):
        for c in fixtures():
            n,t=observe(c);verify(c,n);n.pop('max_ammo_scaling')
            with self.subTest(duration=c['contract']['duration']):self.assertEqual((n,t),bare(c))
    def test_original_effects_are_not_rewritten(self):
        for c in fixtures():
            p=engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True))
            effects=[row['effect'] for row in p['effects']]
            scaled=[e for e in effects if e.get('scaling')=='max_ammo_count'];fixed=[e for e in effects if e.get('stat')=='dealt_fixed_damage']
            self.assertEqual(len(scaled),1);self.assertEqual(len(fixed),1)
            self.assertEqual(scaled[0]['name'],'미정령의 축복 2');self.assertEqual(scaled[0]['duration_bullets'],1)
            self.assertEqual(scaled[0]['trigger']['timing'],['full_charge_fire']);self.assertEqual(scaled[0]['values']['10'],2.01)
if __name__=='__main__':unittest.main()
