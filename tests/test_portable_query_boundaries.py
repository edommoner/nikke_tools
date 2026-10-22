"""Reject accidental math/signature/macro changes in the boundary-only candidate."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_query_boundary_contract import verify

class QueryBoundaryTests(unittest.TestCase):
    def test_only_six_annotations_are_added_to_original_source(self):
        result=verify(ROOT);self.assertTrue(result['verified']);self.assertEqual(len(result['functions']),6);self.assertTrue(result['original_file_tokens_preserved'])
    def test_removed_boundary_is_rejected(self):
        name='gpu/quantity_runtime.slang';s=(ROOT/name).read_text().replace('[noinline]\nuint64_t plainQuantity','uint64_t plainQuantity')
        with self.assertRaisesRegex(AssertionError,'boundary'):verify(ROOT,sources={name:s})
    def test_changed_state_predicate_is_rejected(self):
        name='gpu/ammo_instant_runtime.slang';s=(ROOT/name).read_text().replace('s.modeCapacityEpoch[who] == s.modeEpoch[who]','s.modeCapacityEpoch[who] != s.modeEpoch[who]')
        with self.assertRaisesRegex(AssertionError,'statements'):verify(ROOT,sources={name:s})
    def test_changed_inout_or_callback_argument_is_rejected(self):
        for name,old,new in [('gpu/world_actor_fields.slang','inout Runtime s','Runtime s'),('gpu/world_actor_pools.slang','actorSetCapture(s,mask,index)','actorSetCapture(s,mask,index+1)')]:
            with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'statements'):verify(ROOT,sources={name:(ROOT/name).read_text().replace(old,new,1)})

if __name__=='__main__':unittest.main()
