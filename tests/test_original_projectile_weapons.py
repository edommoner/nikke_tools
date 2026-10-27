"""Original definitions stay intact; physical identity and shared oracle stay exact."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('original_projectile_weapon_tests',ROOT/'research/verify-original-projectile-weapons.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
from portable_original_projectile_weapon_cases import fixtures,prepare

class OriginalProjectileWeapons(unittest.TestCase):
    def test_all_original_definitions_and_owners_survive_static_lowering(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('Packing must not execute CPU battle')):
            for case in fixtures():
                with self.subTest(case=case['name']):
                    c,p=prepare(case);before=copy.deepcopy(c)
                    w,meta,bindings,descriptor=adapter.compile_coordinate_typed(p,c['typed_bindings'],probe_kind=2,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
                    original=c['original_run']['prepared']
                    self.assertEqual(c,before);self.assertEqual(p['effects'],original['effects'])
                    self.assertEqual(c['effects'],[e['effect'] for e in original['effects']])
                    self.assertEqual(c['owners'],[c['names'].index(e['owner']) for e in original['effects']])
                    self.assertEqual(p['policies']['config'],original['policies']['config'])
                    self.assertEqual(len(w),115680);self.assertEqual(w[109968+5120],0xffffffff)
                    self.assertEqual(set(meta['binding_source_indices']),set(range(len(c['effects']))))
                    axes=w[109968+5168:109968+5424]
                    for i,e in enumerate(c['effects']):self.assertEqual(axes[i],2 if e.get('stat')=='projectile_dmg_pct' else 0)
                    self.assertFalse(any(axes[len(c['effects']):]));self.assertFalse(c['declared_owner_counter'])
                    self.assertTrue(all(b['kind']==2 and b['owner']==[0,0,1] for b in c['typed_bindings']))
    def test_control_has_no_typed_spawn_during_battle(self):
        rows=fixtures();self.assertEqual(len(rows),8)
        control=rows[-1];self.assertGreater(control['patterns'][0]['delay'],control['body']['duration'])
        self.assertEqual(control['body']['enemy']['patterns'],control['patterns'])
        for key in ('squad','profile','burst_gauge_mode','seed'):self.assertEqual(control['body'][key],rows[0]['body'][key])
    def test_reuse_resolves_direct_native_and_complete_comparison_context(self):
        from portable_parent_oracles import provider
        c,p=prepare(fixtures()[2]);domain=(c,{},(),None)
        target=provider(adapter,domain)
        self.assertIs(target[2],adapter.native_reference);self.assertIs(target[3],domain)
        self.assertIs(adapter.NATIVE_COMPARISON_CONTEXT,adapter.base.NATIVE_COMPARISON_CONTEXT)
        self.assertEqual(adapter.base.parent.parent.__file__,str(ROOT/'research/verify-coordinate-typed-aim-short.py'))
    def test_actor_policy_is_required_and_never_implicit(self):
        c,p=prepare(fixtures()[2]);p['typed_actor_policy']=None
        with self.assertRaises(ValueError):adapter.compile_coordinate_typed(p,c['typed_bindings'],probe_kind=2,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
if __name__=='__main__':unittest.main()
