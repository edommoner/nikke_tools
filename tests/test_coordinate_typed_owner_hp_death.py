"""HP death fixture provenance and transparency of the passive witness."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_coordinate_typed_owner_hp_death_cases import fixtures,prepare

class OwnerHpDeathTests(unittest.TestCase):
    def test_original_definitions_and_actual_hp_model(self):
        self.assertEqual(len(fixtures()),3)
        for row in fixtures():
            c,_=prepare(row);original=c['original_run']['prepared']['effects']
            self.assertEqual(len(original),71);self.assertEqual(c['effects'][:71],[r['effect'] for r in original]);self.assertEqual(len(c['effects']),73)
            node=next(n for n in c['patterns'] if n['id']=='owner-adds')
            self.assertEqual(node['spec']['hp'],c['owner_hp_death']['hp']);self.assertNotIn('until',node);self.assertNotIn('hit_hp',node['spec'])
    def test_shared_wire_packs_full_case_without_mutation(self):
        from portable_coordinate_typed_input import compile_coordinate_typed
        for row in fixtures():
            c,p=prepare(row);before=copy.deepcopy(p)
            w,m,_,_=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True,coordinate_logical_owners=True)
            self.assertEqual(p,before);self.assertEqual(len(w),115680);self.assertEqual(len(m['binding_source_indices']),73)
    def test_passive_hp_witness_preserves_native_and_trace(self):
        from world_coordinate_typed_owner_add_lifetime_native import observe as base
        from world_coordinate_typed_owner_hp_death_native import observe
        c,_=prepare(fixtures()[2]);before=copy.deepcopy(c)
        a,at=base(copy.deepcopy(c));b,bt=observe(copy.deepcopy(c));witness=b.pop('owner_hp_death')
        self.assertTrue(witness['hits']);self.assertEqual(a,b);self.assertEqual(at,bt);self.assertEqual(c,before)
        from portable_coordinate_typed_owner_hp_death_contracts import verify
        b['owner_hp_death']=witness;self.assertTrue(verify(c,b)['verified'])
        changed=copy.deepcopy(b)
        for hit in changed['owner_hp_death']['hits']:
            if hit['label']=='__enemy__:owner-adds#2':
                for state in hit['after']:state['graph_active']=False
        with self.assertRaises(AssertionError):verify(c,changed)

if __name__=='__main__':unittest.main()
