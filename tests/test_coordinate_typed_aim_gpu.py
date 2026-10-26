"""Static typed aim input, retained-source inverse and complete arena checks."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_typed_aim_gpu_cases import fixtures
from portable_coordinate_typed_weapon_cases import prepare
from portable_coordinate_typed_input import compile_coordinate_typed

class TypedAimInputTests(unittest.TestCase):
    def test_static_wire_last_slot_and_original_input_immutability(self):
        from calculator import timeline
        from portable_backend import validate_composed_stride
        for row in fixtures():
            c,p=prepare(row);before=copy.deepcopy(p)
            with patch.object(timeline,'simulate',side_effect=AssertionError('CPU battle forbidden')):
                w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True)
            self.assertEqual(p,before);self.assertEqual(len(w),115680);self.assertEqual(w[109968+13:109968+15],[1,1])
            self.assertTrue(m['coordinate_typed_input']['automatic_typed_weapon_aim'])
            self.assertEqual(w[109968+5424:109968+5680],[0]*256)
            self.assertEqual(len(m['binding_source_indices']),len(p['effects']))
            if row['name'].endswith('manual-last-slot'):
                self.assertEqual(d['typed_aim_slots']['typed-back'],256);self.assertEqual(w[108792+32],256);self.assertGreater(c['patterns'][0]['until']['time'],c['duration']);self.assertEqual(d['typed_aim_add_slot'],257)
        validate_composed_stride('gpu/world_coordinate_typed_aim_entry.slang',115680,2032000)
    def test_recipient_and_alias_boundaries_fail_closed(self):
        from portable_coordinate_typed_aim_cases import fixtures as cpu
        c,p=prepare(cpu()[-1])
        with self.assertRaisesRegex(ValueError,'logical enemy recipient'):
            compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True)
        for alias in ('core','__enemy__','__enemy__:*'):
            c,p=prepare(fixtures()[0]);c['typed_bindings'][0]['label']=alias
            with self.assertRaises(ValueError):compile_coordinate_typed(p,c['typed_bindings'],geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True)
    def test_native_logical_namespace_is_distinct_from_typed_shapes(self):
        from types import SimpleNamespace
        from coordinate_typed_aim_runtime import TypedCoordinateAim
        scope=TypedCoordinateAim({}, {}, dict(mode='typed-before-body-v1'))
        for alias in ('__enemy__','__enemy__:*'):
            boss=SimpleNamespace(target_kinds={},_nikke_typed_world=SimpleNamespace(bindings=[SimpleNamespace(label=alias)]))
            with self.assertRaisesRegex(ValueError,'logical enemy'):scope.validate_namespace(boss)
    def test_reviewed_inverse_and_arena_reject_overlap(self):
        from portable_coordinate_typed_aim_source_contract import ledger,project_sources,project_backend_source
        from portable_coordinate_typed_aim_specs import check_layout,regions
        from portable_arena_specs import audit_regions,Region
        data=ledger(ROOT);out=project_sources(ROOT)
        for name,row in data['sources'].items():
            if name.endswith('.slang'):
                self.assertEqual(out[name],row['baseline'])
                with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n// unexpected\n'})
        self.assertEqual(project_backend_source(ROOT),data['sources']['app/portable_backend.py']['baseline'])
        plan=check_layout(ROOT);self.assertEqual(plan['focus_id_bits'],9);self.assertEqual(plan['extra_runtime_bytes'],0)
        rows,iw,ow=regions();self.assertFalse(audit_regions(rows+[Region('output','overlap',1769856+220224,1)],iw,ow)['address_plan_verified'])

if __name__=='__main__':unittest.main()
