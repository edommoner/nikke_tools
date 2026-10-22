"""Reject math/signature/macro changes outside the reviewed scope snapshot delta."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_query_boundary_contract import verify

class QueryBoundaryTests(unittest.TestCase):
    def test_six_annotations_and_only_reviewed_snapshot_delta_preserve_baseline_tokens(self):
        result=verify(ROOT);self.assertTrue(result['verified']);self.assertEqual(len(result['functions']),6);self.assertFalse(result['original_file_tokens_preserved']);self.assertTrue(result['unmodified_tokens_preserved']);self.assertTrue(result['explicit_scope_snapshot_delta'])
    def test_altered_scope_snapshot_helper_or_use_is_rejected(self):
        name='gpu/world_actor_state.slang';source=(ROOT/name).read_text()
        for old,new in [('return results[at];','return results[at+1];'),('actorStateQueryScopeSnapshot(at);','actorStateQueryScopeSnapshot(at+1);'),('[noinline]\nuint actorStateQueryScopeSnapshot','uint actorStateQueryScopeSnapshot')]:
            with self.subTest(old=old),self.assertRaisesRegex(AssertionError,'statements'):verify(ROOT,sources={name:source.replace(old,new,1)})
    def test_only_exact_private_interrupt_admission_delta_is_allowed(self):
        self.assertTrue(verify(ROOT)['explicit_interrupt_pool_delta'])
        name='gpu/world_actor_pools.slang';source=(ROOT/name).read_text()
        for old,new in [('kind==1||kind==6 ? mode!=1','kind==1||kind==2 ? mode!=1'),('kind!=1 && kind!=6 && (n!=0','kind!=1 && kind!=2 && (n!=0')]:
            self.assertIn(old,source)
            with self.subTest(old=old),self.assertRaisesRegex(AssertionError,'statements'):verify(ROOT,sources={name:source.replace(old,new,1)})
    def test_private_numeric_view_must_not_alias_projectile(self):
        self.assertTrue(verify(ROOT)['explicit_interrupt_field_delta'])
        name='gpu/world_actor_fields.slang';source=(ROOT/name).read_text()
        with self.assertRaisesRegex(AssertionError,'statements'):verify(ROOT,sources={name:source.replace('if(commands[b]==6)','if(commands[b]==2)',1)})
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
