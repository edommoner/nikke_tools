"""New logical ownership needs an explicit wire and strict source inverse."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_typed_logical_owner_cases import fixtures,prepare
from portable_coordinate_typed_input import compile_coordinate_typed

def compile_case(c,p,**changes):
    args=dict(probe_kind=c['logical_owner_contract']['kind'],geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True,coordinate_logical_owners=True);args.update(changes)
    return compile_coordinate_typed(p,c['typed_bindings'],**args)

class LogicalOwnerGPUTests(unittest.TestCase):
    def test_complete_originals_pack_without_running_native(self):
        from calculator import timeline
        from portable_backend import validate_composed_stride
        for row in fixtures():
            c,p=prepare(row);before=copy.deepcopy(p)
            with patch.object(timeline,'simulate',side_effect=AssertionError('Native forbidden in packing')):w,m,actors,scene=compile_case(c,p)
            self.assertEqual(p,before);self.assertEqual(len(w),115680)
            self.assertEqual(w[109968+12:109968+16],[3,1,1,2]);self.assertEqual(w[109968+2328+5:109968+2328+8],[5,1,1])
            self.assertEqual(len(m['binding_source_indices']),73)
        validate_composed_stride('gpu/world_coordinate_typed_logical_owner_entry.slang',115680,2032000)
    def test_policy_and_consumer_are_both_explicit(self):
        c,p=prepare(fixtures()[0])
        for flags in (dict(coordinate_logical_owners=False),dict(coordinate_typed_owners=False),dict(coordinate_logical_owners=1)):
            with self.assertRaises(ValueError):compile_case(c,p,**flags)
        p['typed_actor_policy']={'mode':'body-owned-current-fields-v1'}
        with self.assertRaises(ValueError):compile_case(c,p)
    def test_predicate_view_uses_owner_without_changing_physical_row(self):
        import detail_gpu
        from portable_coordinate_typed_owner_input import compiler_policy
        from coordinate_typed_actor_policy import LOGICAL_FIELD_MODE
        marker=[0]*344;marker[2]=87;marker[296:299]=[3,10,1]
        child=[0]*344;child[14]=1
        from world_condition_specs import TARGET_IS_ADD
        child[15]=TARGET_IS_ADD;rows=[marker,child];original=detail_gpu.validate_target_predicate_policies;before=copy.deepcopy(rows)
        bindings=[dict(kind=3,identity=10,owner=[5,1,1])]
        with compiler_policy(bindings,{'mode':LOGICAL_FIELD_MODE}):
            detail_gpu.validate_target_predicate_policies(rows);self.assertEqual(rows,before)
            bad=copy.deepcopy(rows);bad[0][297]=11
            with self.assertRaises(ValueError):detail_gpu.validate_target_predicate_policies(bad)
        self.assertIs(detail_gpu.validate_target_predicate_policies,original)
    def test_source_inverse_is_exact_and_arena_is_unchanged(self):
        from portable_coordinate_typed_logical_owner_source_contract import ledger,project_sources,project_backend_source
        data=ledger(ROOT);old=project_sources(ROOT)
        for name,row in data['sources'].items():
            if name.endswith('.slang'):
                self.assertEqual(old[name],row['baseline'])
                with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n// unreviewed\n'})
        self.assertEqual(project_backend_source(ROOT),data['sources']['app/portable_backend.py']['baseline'])
        from portable_coordinate_typed_aim_specs import check_layout
        layout=check_layout(ROOT);self.assertEqual(layout['extra_runtime_bytes'],0);self.assertEqual(layout['extra_output_words'],0)

if __name__=='__main__':unittest.main()
