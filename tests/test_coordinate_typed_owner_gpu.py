"""Explicit owned-field wire, untouched original definitions and strict source inverse."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_typed_owner_cases import fixtures,prepare
from portable_coordinate_typed_input import compile_coordinate_typed

def compile_case(c,p,**kwargs):
    return compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,**kwargs)

class OwnerInputTests(unittest.TestCase):
    def test_all_original_definitions_and_explicit_header_without_cpu_schedule(self):
        from calculator import timeline
        from portable_backend import validate_composed_stride
        for row in fixtures():
            c,p=prepare(row);self.assertTrue(c['observe_actor_status']);before=copy.deepcopy(p)
            with patch.object(timeline,'simulate',side_effect=AssertionError('CPU battle forbidden')):w,m,b,d=compile_case(c,p,coordinate_typed_owners=True)
            self.assertEqual(p,before);self.assertEqual(len(w),115680);self.assertEqual(w[109968+12:109968+16],[1,1,1,2]);self.assertEqual(len(m['binding_source_indices']),71+len(c['declared_owner_counter']))
            self.assertEqual(w[109968+2328+5:109968+2328+8],[0,0,1])
        validate_composed_stride('gpu/world_coordinate_typed_owner_entry.slang',115680,2032000)
    def test_policy_is_not_inferred_and_bad_owner_cannot_be_admitted(self):
        c,p=prepare(fixtures()[1])
        with self.assertRaisesRegex(ValueError,'new shared GPU consumer'):compile_case(c,p)
        for value in (1,None,'yes'):
            with self.assertRaisesRegex(ValueError,'Explicit typed owner'):compile_case(c,p,coordinate_typed_owners=value)
        for owner in (None,[5,0,1],[0,0,2]):
            bad=copy.deepcopy(c);bad['typed_bindings'][0]['owner']=owner
            with self.assertRaisesRegex(ValueError,'BODY-owned'):compile_case(bad,p,coordinate_typed_owners=True)
        bad=copy.deepcopy(p);bad['typed_actor_policy']={'mode':'canonical-current-damage-v1'}
        with self.assertRaisesRegex(ValueError,'explicit actor policy'):compile_case(c,bad,coordinate_typed_owners=True)
    def test_private_predicate_policy_preserves_physical_rows_and_restores_guard(self):
        import detail_gpu
        from portable_coordinate_typed_owner_input import compiler_policy
        from world_condition_specs import TARGET_IS_BOSS
        counter=[0]*344;counter[2]=87;counter[296:299]=[3,10,1]
        field=[0]*344;field[14]=1;field[15]=TARGET_IS_BOSS
        rows=[counter,field];before=copy.deepcopy(rows);original=detail_gpu.validate_target_predicate_policies
        with self.assertRaisesRegex(ValueError,'explicit actor policy'):original(rows)
        bindings=[dict(kind=3,identity=10,owner=[0,0,1])]
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with compiler_policy(bindings):
                detail_gpu.validate_target_predicate_policies(rows);self.assertEqual(rows,before)
                bad=copy.deepcopy(rows);bad[0][297]=11
                with self.assertRaisesRegex(ValueError,'declared BODY-owned'):detail_gpu.validate_target_predicate_policies(bad)
                raise RuntimeError('injected')
        self.assertIs(detail_gpu.validate_target_predicate_policies,original)

    def test_exact_new_source_inverse_and_preserved_arena(self):
        from portable_coordinate_typed_owner_source_contract import ledger,project_sources,project_backend_source
        from portable_coordinate_typed_aim_specs import check_layout
        data=ledger(ROOT);old=project_sources(ROOT)
        for name,row in data['sources'].items():
            if name.endswith('.slang'):
                self.assertEqual(old[name],row['baseline'])
                with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n// unreviewed\n'})
        self.assertEqual(project_backend_source(ROOT),data['sources']['app/portable_backend.py']['baseline'])
        layout=check_layout(ROOT);self.assertEqual(layout['extra_runtime_bytes'],0);self.assertEqual(layout['extra_output_words'],0)

if __name__=='__main__':unittest.main()
