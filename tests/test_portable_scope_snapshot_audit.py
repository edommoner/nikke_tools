"""A pointer retained across the update must never count as a saved scalar."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_scope_snapshot_audit import audit

GOOD=b'''static __device__ __noinline__ uint actorStateQueryScopeSnapshot_0(uint at) { return *p; }
uint actorStatePushQuery_0(uint target) {
uint previous=actorStateQueryScopeSnapshot_0(at);
*p = target+1;
return previous;
}'''

class ScopeSnapshotAuditTests(unittest.TestCase):
    def test_scalar_value_before_store_is_distinct_from_calculation_proof(self):
        r=audit(GOOD,GOOD);self.assertTrue(r['generated_scope_snapshot_verified']);self.assertFalse(r['calculation_verified'])
    def test_old_cuda_retained_pointer_cannot_pass(self):
        bad=GOOD.replace(b'uint previous=actorStateQueryScopeSnapshot_0(at);',b'uint* previous=p;').replace(b'return previous;',b'return *previous;')
        with self.assertRaises(ValueError):audit(bad,GOOD)
    def test_post_store_snapshot_or_removed_noinline_rejected(self):
        bad=GOOD.replace(b'uint previous=actorStateQueryScopeSnapshot_0(at);\n*p = target+1;',b'*p = target+1;\nuint previous=actorStateQueryScopeSnapshot_0(at);')
        for raw in (bad,GOOD.replace(b'__noinline__',b'')):
            with self.assertRaises(ValueError):audit(raw,GOOD)
    def test_wrong_return_value_or_writing_snapshot_helper_rejected(self):
        for raw in (GOOD.replace(b'return previous;',b'return *p;'),GOOD.replace(b'{ return *p; }',b'{\n*p = 1;\nreturn *p; }')):
            with self.assertRaises(ValueError):audit(raw,GOOD)

if __name__=='__main__':unittest.main()
