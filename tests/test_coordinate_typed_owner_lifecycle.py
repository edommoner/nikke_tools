"""Data-only lifecycle inputs plus transparency of passive query observation."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_typed_owner_lifecycle_cases import fixtures,prepare
from portable_coordinate_typed_input import compile_coordinate_typed

class LifecycleTests(unittest.TestCase):
    def test_all_original_definitions_compile_to_existing_wire_without_state_schedule(self):
        rows=fixtures();self.assertEqual(len(rows),8)
        for row in rows:
            c,p=prepare(row);before=copy.deepcopy(p);kind=c['owner_lifecycle']['kind']
            w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=kind,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
            self.assertEqual(p,before);self.assertEqual(len(w),115680);self.assertEqual(w[109968+12:109968+16],[1,1,1,2]);self.assertEqual(len(m['binding_source_indices']),71+len(c['declared_owner_counter']))
            self.assertEqual(c['body']['seed'],4401)
    def test_dead_and_stale_are_authored_lifecycles_not_forged_notifications(self):
        for c in fixtures():
            p=c['owner_lifecycle']
            if p['dead_query']:self.assertEqual(c['typed_bindings'][0]['capacity'],1.)
            if p['stale_filter']:
                self.assertEqual(c['patterns'][0]['repeat'],4);self.assertEqual(c['declared_owner_counter'][0]['trigger']['timing'],['every:1.25s']);self.assertEqual(c['declared_owner_counter'][0]['target_counter']['actor']['generation'],1)
    def test_passive_lifetime_probe_preserves_complete_original_native_values(self):
        from world_coordinate_typed_owner_native import observe as plain
        from world_coordinate_typed_owner_lifecycle_native import observe
        c,p=prepare(fixtures()[0]);before,_=plain(copy.deepcopy(c));after,_=observe(copy.deepcopy(c));rows=after.pop('owner_query_lifetimes')
        self.assertEqual(before,after);self.assertTrue(rows);self.assertTrue(all(r['alive'] for r in rows))

if __name__=='__main__':unittest.main()
