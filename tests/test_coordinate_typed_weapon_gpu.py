"""Static physical input and historical proof boundaries before GPU dispatch."""
import copy,hashlib,sys,unittest,importlib.util
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_typed_weapon_cases import fixtures,prepare
from portable_coordinate_typed_input import compile_coordinate_typed

class TypedWeaponInputTests(unittest.TestCase):
    def test_weapon_only_arena_ownership_and_overlap_rejection(self):
        from portable_coordinate_typed_weapon_specs import check_layout,regions
        from portable_arena_specs import audit_profile,audit_regions,Region
        plan=check_layout(ROOT);self.assertEqual((plan['input_words'],plan['output_words']),(115680,2032000))
        self.assertEqual((plan['extra_runtime_bytes'],plan['extra_output_words']),(0,0))
        self.assertTrue(plan['all_records_hashed']);self.assertTrue(plan['weapon_only_requires_zero_skill_routes'])
        self.assertTrue(audit_profile('coordinate-typed-weapon-v1')['address_plan_verified'])
        rows,iw,ow=regions();self.assertFalse(audit_regions(rows+[Region('output','overlap',1769856+171040,1)],iw,ow)['address_plan_verified'])
    def test_original_definitions_no_skill_probe_or_schedule_and_complete_wire(self):
        from calculator import timeline
        from portable_backend import validate_composed_stride
        for row in fixtures():
            c,p=prepare(row);before=copy.deepcopy(p)
            with patch.object(timeline,'simulate',side_effect=AssertionError('CPU schedule forbidden')):
                words,meta,actors,scene=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=c['typed_bindings'][0]['kind'],geometry=c['typed_geometry'],coordinate_weapon_targets=True)
            self.assertEqual(p,before);self.assertEqual(len(words),115680)
            self.assertEqual(words[109968+5120],0xffffffff);self.assertEqual(words[109968+13],1)
            self.assertEqual(words[109968+5424:109968+5680],[0]*256)
            self.assertEqual(len(meta['binding_source_indices']),len(p['effects']))
            self.assertFalse(meta['coordinate_typed_input']['automatic_typed_weapon_aim'])
        validate_composed_stride('gpu/world_coordinate_typed_weapon_entry.slang',115680,2032000)
        with self.assertRaises(ValueError):validate_composed_stride('gpu/world_coordinate_typed_weapon_entry.slang',115679,2032000)
    def test_incompatible_point_growth_and_skill_probe_are_rejected(self):
        c,p=prepare(fixtures()[0]);base=dict(probe_kind=2,coordinate_weapon_targets=True)
        for geometry in (dict(point=[0.,0.],shapes=c['typed_geometry']['shapes']),dict(c['typed_geometry'],grow=1.)):
            with self.assertRaises(ValueError):compile_coordinate_typed(p,c['typed_bindings'],geometry=geometry,**base)
        with self.assertRaises(ValueError):compile_coordinate_typed(p,c['typed_bindings'],0,geometry=c['typed_geometry'],**base)
    def test_reviewed_hook_inverse_and_unreviewed_changes(self):
        from portable_coordinate_typed_weapon_source_contract import ledger,project_sources,project_backend_source
        data=ledger(ROOT);old=project_sources(ROOT)
        for name,row in data['sources'].items():
            if name.endswith('.slang'):
                self.assertEqual(hashlib.sha256(old[name].encode()).hexdigest(),row['baseline_sha256'])
                with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n// unreviewed\n'})
        self.assertEqual(project_backend_source(ROOT),data['sources']['app/portable_backend.py']['baseline'])
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n# unreviewed\n')
    def test_existing_python_filter_keeps_complete_native_fingerprint(self):
        s=importlib.util.spec_from_file_location('typed_weapon_profile_test',ROOT/'research/verify-coordinate-typed-weapon-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        import native_python_profile as profiles
        rows,_=a.prepare();domain=next(d for name,_,d in rows if name=='coordinate-typed-weapon/projectile-front')
        before=len(profiles.RECEIPTS);filtered=a.native_reference(domain)
        self.assertEqual(len(profiles.RECEIPTS),before+1);receipt=profiles.RECEIPTS[-1]
        self.assertTrue(receipt['python_observer_order_preserved']);self.assertGreater(receipt['event_counts']['c_call'],0)
        domain[0]['python_observers_only']=False;ordinary=a.native_reference(domain)
        self.assertEqual(filtered,ordinary)
    def test_live_preflight_cache_uses_the_actual_delegated_call_site(self):
        from portable_parent_oracles import provider
        s=importlib.util.spec_from_file_location('typed_weapon_owner_test',ROOT/'research/verify-coordinate-typed-weapon-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        rows,_=a.prepare()
        old=next(d for _,_,d in rows if d is not None and not d[0].get('coordinate_weapon_targets'))
        new=next(d for _,_,d in rows if d is not None and d[0].get('coordinate_weapon_targets'))
        self.assertIs(provider(a,old)[0],a.parent.compare.__globals__)
        self.assertIs(provider(a,new)[0],a.compare.__globals__)

if __name__=='__main__':unittest.main()
