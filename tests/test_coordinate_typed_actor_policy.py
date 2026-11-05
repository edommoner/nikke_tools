"""Current damage policy is explicit; enemy fields are not silently admitted."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from coordinate_typed_actor_policy import normalize,validate_effects
from portable_coordinate_typed_actor_cases import fixtures
from portable_coordinate_typed_weapon_cases import prepare

class ActorPolicyTests(unittest.TestCase):
    def test_policy_and_original_damage_admission_are_explicit(self):
        for invalid in (None,True,{},dict(mode='other'),dict(mode='canonical-current-damage-v1',schedule=[])):
            with self.assertRaises(ValueError):normalize(invalid)
        c,_=prepare(fixtures()[1]);before=copy.deepcopy(c['effects'])
        validate_effects(c['effects'],c['typed_actor_policy']);self.assertEqual(c['effects'],before)
        with self.assertRaisesRegex(ValueError,'own actor policy'):validate_effects(c['effects'],None)
        with self.assertRaisesRegex(ValueError,'ownership policy'):validate_effects([dict(type='buff',target='target')],c['typed_actor_policy'])
    def test_cpu_policy_cannot_be_packed_into_the_previous_gpu_consumer(self):
        from portable_coordinate_typed_input import compile_coordinate_typed
        c,p=prepare(fixtures()[1])
        with self.assertRaisesRegex(ValueError,'shared GPU consumer'):
            compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True)
    def test_new_cases_keep_original_trigger_and_declared_worlds(self):
        for row in fixtures():
            c,p=prepare(row);current=[e for e in c['effects'] if e.get('target')=='enemies_nearest_in_range']
            self.assertEqual(len(current),1);self.assertEqual(current[0]['trigger']['timing'],['hit_count:100'])
            self.assertEqual(p['typed_actor_policy'],c['typed_actor_policy']);self.assertEqual(len(p['effects']),len(c['effects']))
            self.assertEqual(c['original_run']['body']['squad'],row['body']['squad'])

if __name__=='__main__':unittest.main()
