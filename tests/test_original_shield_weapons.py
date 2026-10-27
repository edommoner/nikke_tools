"""Preserve every original definition and explicitly declare manual operations."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('original_shield_weapon_tests',ROOT/'research/verify-original-shield-weapons.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
from portable_original_shield_weapon_cases import fixtures,prepare

class OriginalShieldWeapons(unittest.TestCase):
    def test_originals_keep_all_definitions_and_use_only_the_existing_shield_axis(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle during packing')):
            for row in fixtures():
                c,p=prepare(row);before=copy.deepcopy(c)
                w,m,b,d=adapter.compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
                original=c['original_run']['prepared'];self.assertEqual(c,before);self.assertEqual(p['effects'],original['effects'])
                self.assertEqual(c['effects'],[e['effect'] for e in original['effects']]);self.assertEqual(c['owners'],[c['names'].index(e['owner']) for e in original['effects']])
                self.assertEqual(p['policies']['config'],original['policies']['config']);self.assertEqual(p['base_atk'],original['base_atk'])
                self.assertEqual(len(w),115680);self.assertEqual(w[109968+5120],0xffffffff)
                self.assertEqual(set(m['binding_source_indices']),set(range(len(c['effects']))))
                axes=w[109968+5168:109968+5424]
                for i,e in enumerate(c['effects']):self.assertEqual(axes[i],3 if e.get('stat')=='shield_dmg_pct' else 0)
                self.assertFalse(any(axes[len(c['effects']):]));self.assertFalse(c['declared_owner_counter'])
                self.assertTrue(all(b['kind']==3 and b['owner']==[0,0,1] for b in c['typed_bindings']))
    def test_cover_is_an_explicit_operation_after_original_identity_not_a_new_effect(self):
        rows=fixtures();self.assertEqual(len(rows),10)
        for row in rows[-2:]:
            c,p=prepare(row);original=c['original_run']['prepared']
            self.assertNotIn('sequence',original['chars'][0]['control'])
            self.assertEqual(p['chars'][0]['control']['sequence'],c['declared_manual_sequences'][c['names'][0]])
            self.assertEqual(c['controls'][0],p['chars'][0]['control'])
            for a,b in zip(original['chars'],p['chars'],strict=True):
                self.assertEqual({k:v for k,v in a.items() if k!='control'},{k:v for k,v in b.items() if k!='control'})
            self.assertEqual(c['body']['enemy']['patterns'],c['patterns'])
    def test_original_native_provider_and_full_comparison_context_are_reused(self):
        from portable_parent_oracles import provider
        c,p=prepare(fixtures()[0]);domain=(c,{},(),None)
        target=provider(adapter,domain);self.assertIs(target[2],adapter.native_reference);self.assertIs(target[3],domain)
        self.assertIs(adapter.NATIVE_COMPARISON_CONTEXT,adapter.base.NATIVE_COMPARISON_CONTEXT)
        self.assertEqual(Path(adapter.base.base.parent.parent.__file__).name,'verify-coordinate-typed-aim-short.py')
    def test_owner_is_never_invented_or_taken_from_a_stale_generation(self):
        c,p=prepare(fixtures()[0])
        for owner in (None,[0,0,2],[5,0,1]):
            bindings=copy.deepcopy(c['typed_bindings']);bindings[0]['owner']=owner
            with self.assertRaises(ValueError):adapter.compile_coordinate_typed(p,bindings,probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
if __name__=='__main__':unittest.main()
