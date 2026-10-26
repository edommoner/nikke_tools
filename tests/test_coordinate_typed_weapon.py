"""Real canonical weapon routing and restoration before a GPU port is accepted."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_typed_weapon_cases import fixtures
from portable_coordinate_typed_weapon_contracts import verify
from world_coordinate_typed_weapon_native import observe

class CoordinateTypedWeaponTests(unittest.TestCase):
    def test_real_weapons_frozen_shots_and_sampled_rng(self):
        from calculator import timeline
        saved=(timeline.CharState._coord_pellet,timeline.calc_damage,timeline.HitEvent,timeline.simulate)
        for case in fixtures():
            with self.subTest(case=case['name']):
                before=copy.deepcopy(case);native,_=observe(case);contract=verify(case,native)
                self.assertTrue(contract['verified']);self.assertFalse(contract['gpu_supported'])
                self.assertEqual(case,before)
                self.assertEqual(saved,(timeline.CharState._coord_pellet,timeline.calc_damage,timeline.HitEvent,timeline.simulate))
    def test_expected_mode_and_incompatible_policies_rejected(self):
        from calculator import timeline
        from coordinate_typed_weapon_runtime import CoordinateWeaponShots
        from destructible_battle_runtime import typed_battle
        data=dict(worlds=[],managers=[]);geometry=dict(point_source='caster_aim',shapes=[dict(x=0.,y=0.,r=1.)])
        for spec in (None,dict(point=[0.,0.]),dict(geometry,grow=1.)):
            with self.assertRaises(ValueError):CoordinateWeaponShots(timeline,data,spec)
        original=timeline.CharState._coord_pellet
        shots=CoordinateWeaponShots(timeline,data,geometry)
        with shots.scope(),self.assertRaisesRegex(ValueError,'actual sampled'):
            timeline.CharState._coord_pellet(None,None,0.,None,{}, {}, {},True,None,{})
        self.assertIs(timeline.CharState._coord_pellet,original)
        with self.assertRaisesRegex(ValueError,'explicit geometry/modifier'):
            with typed_battle([],coordinate_weapon_targets=True):pass
    def test_packet_generation_rng_and_notification_corruption_is_rejected(self):
        case=fixtures()[0];native,_=observe(case)
        def amount(n):n['coordinate_typed_weapon']['attacks'][0]['damage']+=1.
        def handle(n):n['coordinate_typed_weapon']['attacks'][0]['receipts'][0]['handle'][2]+=1
        def rng(n):n['physical_rng']['state'][0]^=1
        def order(n):n['coordinate_typed_weapon']['full_charge_boundaries'][0]['landed_same_shot']=1
        for corrupt in (amount,handle,rng,order):
            with self.subTest(corrupt=corrupt.__name__),self.assertRaises(AssertionError):
                changed=copy.deepcopy(native);corrupt(changed);verify(case,changed)
    def test_cpu_contract_does_not_promote_missing_gameplay_or_gpu_support(self):
        from portable_readiness_semantics import reference_readiness
        for stat in ('projectile_dmg_pct','shield_dmg_pct'):
            result=reference_readiness(dict(phase='effect',kind='buff',stat=stat,target='self'))
            self.assertEqual(result['lane'],'reference_model_gap');self.assertFalse(result['gpu_supported'])
            row=result['typed_coordinate_weapon_reference'];self.assertTrue(row['cpu_contract_verified'])
            for flag in ('metal_verified','cuda_device_verified','automatic_typed_weapon_aim_verified','canonical_consumer_verified','in_game_rules_verified','full_character_verified'):
                self.assertFalse(row[flag])

if __name__=='__main__':unittest.main()
