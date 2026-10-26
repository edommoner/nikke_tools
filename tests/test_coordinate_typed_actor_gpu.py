"""Current damage flag, complete original definitions and retained-source audit."""
import copy,hashlib,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_typed_actor_cases import fixtures
from portable_coordinate_typed_weapon_cases import prepare
from portable_coordinate_typed_input import compile_coordinate_typed

class ActorInputTests(unittest.TestCase):
    def test_original_skill_and_complete_static_input(self):
        from calculator import timeline
        from portable_backend import validate_composed_stride
        for row in fixtures():
            c,p=prepare(row);before=copy.deepcopy(p)
            with patch.object(timeline,'simulate',side_effect=AssertionError('CPU battle forbidden')):
                w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True)
            self.assertEqual(p,before);self.assertEqual(len(w),115680);self.assertEqual(w[109968+13:109968+16],[1,1,1])
            self.assertEqual(len(m['binding_source_indices']),73);self.assertEqual(w[109968+5424:109968+5680],[0]*256)
            self.assertEqual(p['effects'][1]['effect']['target'],'enemies_nearest_in_range');self.assertEqual(p['effects'][1]['effect']['trigger']['timing'],['hit_count:100'])
        validate_composed_stride('gpu/world_coordinate_typed_actor_entry.slang',115680,2032000)
    def test_policy_cannot_admit_current_enemy_fields(self):
        c,p=prepare(fixtures()[0]);p['effects'][1]['effect']['type']='buff'
        with self.assertRaisesRegex(ValueError,'ownership policy'):
            compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True)
        with self.assertRaisesRegex(ValueError,'frame aim'):
            compile_coordinate_typed(p,c['typed_bindings'],coordinate_typed_actors=True)
    def test_exact_source_inverse_and_unchanged_arena(self):
        from portable_coordinate_typed_actor_source_contract import ledger,project_sources,project_backend_source
        from portable_coordinate_typed_aim_specs import check_layout
        data=ledger(ROOT);old=project_sources(ROOT)
        for name,row in data['sources'].items():
            if name.endswith('.slang'):
                self.assertEqual(old[name],row['baseline'])
                with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n// unreviewed\n'})
        self.assertEqual(project_backend_source(ROOT),data['sources']['app/portable_backend.py']['baseline'])
        layout=check_layout(ROOT);self.assertEqual(layout['extra_runtime_bytes'],0);self.assertEqual(layout['extra_output_words'],0)

if __name__=='__main__':unittest.main()
