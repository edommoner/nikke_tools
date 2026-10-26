"""Real frame arbitration plus fail-closed geometry and GPU/reference boundaries."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from coordinate_typed_aim_runtime import normalize,TypedCoordinateAim,AimGeometry
from portable_coordinate_typed_aim_cases import fixtures
from world_coordinate_typed_aim_native import observe
from portable_coordinate_typed_aim_contracts import verify

class TypedAimTests(unittest.TestCase):
    def test_original_rosters_frame_selection_manual_and_focus(self):
        from calculator import timeline
        before=(timeline.CharState._coord_pellet,timeline.HitEvent,timeline.simulate,timeline.BossScript)
        for case in fixtures():
            with self.subTest(case=case['name']):
                unchanged=copy.deepcopy(case);native,_=observe(case);result=verify(case,native)
                self.assertTrue(result['verified']);self.assertFalse(result['gpu_supported']);self.assertEqual(case,unchanged)
                self.assertEqual(before,(timeline.CharState._coord_pellet,timeline.HitEvent,timeline.simulate,timeline.BossScript))
    def test_policy_and_missing_gpu_consumer_are_not_silently_ignored(self):
        from portable_coordinate_typed_weapon_cases import prepare
        from portable_coordinate_typed_input import compile_coordinate_typed
        for invalid in (None,True,{},dict(mode='unknown'),dict(mode='typed-before-body-v1',schedule=[])):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):normalize(invalid)
        c,p=prepare(fixtures()[0])
        with self.assertRaisesRegex(ValueError,'new shared GPU wire'):
            compile_coordinate_typed(p,c['typed_bindings'],geometry=c['typed_geometry'],coordinate_weapon_targets=True)
    def test_aim_centers_do_not_add_skill_targets_or_reset_the_landing_cache(self):
        from calculator import boss_pattern,aim
        target=boss_pattern.GeomTarget('typed','typed_projectile',aim.Shape(x=5.,y=6.,r=1.))
        cached={('old',):object()};base=SimpleNamespace(targets=(),shapes=(),_cache=cached,center=lambda name:None,kind=lambda name:'',landing=lambda *args:cached)
        proxy=AimGeometry(object(),base,[target]);self.assertEqual(proxy.center('typed'),(5.,6.));self.assertEqual(proxy.kind('typed'),'typed_projectile')
        self.assertIs(proxy.targets,base.targets);self.assertIs(proxy.shapes,base.shapes);self.assertIs(proxy._cache,cached);self.assertIs(proxy.landing(1.,2.,3.),cached)
        self.assertEqual(copy.deepcopy(proxy).center('typed'),(5.,6.))
    def test_canonical_mid_frame_replacement_is_never_restored_to_stale_geometry(self):
        from calculator.timeline import GEOM_KEY
        data={};scope=TypedCoordinateAim(data,{},dict(mode='typed-before-body-v1'));boss=SimpleNamespace();old=SimpleNamespace();new=SimpleNamespace()
        scope.owner=boss;scope.time=0.;scope.base=old;scope.proxy=object();boss.geom=new;enemy={GEOM_KEY:new}
        scope.restore(boss,.1,enemy);self.assertIs(boss.geom,new);self.assertIs(enemy[GEOM_KEY],new)
        boss.geom=scope.proxy;scope.restore(boss,.1,enemy);self.assertIs(boss.geom,old)
    def test_undeclared_manual_names_and_core_alias_are_still_rejected(self):
        case=fixtures()[3];owner=case['body']['squad'][0];case['declared_aim_controls'][owner][0]['at']='undeclared'
        with self.assertRaisesRegex(ValueError,'docs/CONTROL'):observe(case)
        case=fixtures()[0];case['typed_bindings'][0]['label']='core'
        with self.assertRaisesRegex(ValueError,'cannot alias'):observe(case)
    def test_reference_metadata_retains_logical_gap_and_gpu_rejection(self):
        from portable_readiness_semantics import reference_readiness
        for stat in ('projectile_dmg_pct','shield_dmg_pct'):
            result=reference_readiness(dict(phase='effect',kind='buff',stat=stat,target='self'))
            self.assertEqual(result['lane'],'reference_model_gap');self.assertFalse(result['gpu_supported'])
            proof=result['typed_coordinate_aim_reference'];self.assertEqual((proof['cases'],proof['positive_contract_cases'],proof['logical_recipient_gap_cases']),(7,6,1))
            for flag in ('gpu_wire_connected','metal_verified','cuda_device_verified','canonical_consumer_verified','in_game_rules_verified','full_character_verified'):
                self.assertFalse(proof[flag])

if __name__=='__main__':unittest.main()
