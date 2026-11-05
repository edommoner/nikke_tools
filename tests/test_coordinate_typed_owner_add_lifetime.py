"""Complete original battle and passive lifetime-observation transparency."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_coordinate_typed_owner_add_lifetime_cases import fixtures,prepare

class OwnerAddLifetimeTests(unittest.TestCase):
    def test_authored_graph_and_original_definitions_are_retained(self):
        rows=fixtures();self.assertEqual(len(rows),4)
        for row in rows:
            c,p=prepare(row);self.assertEqual(c['body']['duration'],8.)
            original=c['original_run']['prepared']['effects'];self.assertEqual(len(original),71)
            self.assertEqual(c['effects'][:71],[r['effect'] for r in original]);self.assertEqual(len(c['effects']),73)
            node=next(n for n in c['patterns'] if n['id']=='owner-adds');self.assertEqual(node['repeat'],c['owner_add_lifetime']['repeat'])
            self.assertEqual(node['until']['time'],c['owner_add_lifetime']['until'])
        self.assertEqual(rows[-1]['declared_owner_counter'][0]['max_trigger'],1)
    def test_existing_shared_wire_packs_full_lifetime_cases(self):
        from portable_coordinate_typed_input import compile_coordinate_typed
        for row in fixtures():
            c,p=prepare(row);before=copy.deepcopy(p)
            w,m,actors,scene=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=c['owner_add_lifetime']['kind'],geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True,coordinate_logical_owners=True)
            self.assertEqual(p,before);self.assertEqual(len(w),115680)
            self.assertEqual(w[109968+12:109968+16],[3,1,1,2]);self.assertEqual(len(m['binding_source_indices']),73)
    def test_passive_observer_does_not_change_complete_native_result(self):
        from world_coordinate_typed_owner_native import observe as plain
        from world_coordinate_typed_owner_add_lifetime_native import observe
        c,_=prepare(fixtures()[1]);before=copy.deepcopy(c);a,at=plain(copy.deepcopy(c));b,bt=observe(copy.deepcopy(c))
        witness=b.pop('owner_add_lifetime');self.assertTrue(witness['field_visibility_transitions'])
        self.assertEqual(a,b);self.assertEqual(at,bt);self.assertEqual(c,before)

if __name__=='__main__':unittest.main()
