"""Use slices of the actual failed/successful generated code as guard fixtures."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_scope_snapshot_audit import audit_staged
DATA=json.loads((Path(__file__).parent/'fixtures/portable-staged-scope-generated.json').read_text())
def pair(label):return [DATA[label][t]['functions'].encode() for t in ('cuda','metal')]
class StagedScopeAuditTests(unittest.TestCase):
    def test_real_old_generated_missing_publication_is_rejected(self):
        with self.assertRaises(ValueError):audit_staged(*pair('missing-publication'))
    def test_real_buffer_publication_is_not_battle_certification(self):
        result=audit_staged(*pair('buffer-scope'));self.assertTrue(result['generated_staged_scope_verified']);self.assertFalse(result['calculation_verified']);self.assertEqual(result['gpu_calls'],0)
    def test_missing_one_snapshot_publication_or_restore_is_rejected(self):
        import re
        good=pair('buffer-scope')
        from portable_scope_snapshot_audit import function
        text=good[0].decode();_,body,_=function(text,'stagedPass')
        snapshots=list(re.finditer(r'\buint\s+(\w+)\s*=\s*stagedScopeSnapshot_\d+\([^;]+;',body))
        self.assertEqual(len(snapshots),4);saved=snapshots[-1].group(1)
        for token in (snapshots[-1].group(0),next(m.group(0) for m in re.finditer(r'(?m)^\s*\*[^;\n]+?\s*=\s*([^;\n]+);',body) if m.group(1).strip()==saved)):
            changed=text.replace(token,'',1);self.assertNotEqual(changed,text)
            with self.assertRaises(ValueError):audit_staged(changed.encode(),good[1])
        text=good[0].decode();dispatch=text.index('dispatch_');last_snapshot=text.rindex('stagedScopeSnapshot_',0,dispatch)
        publications=list(re.finditer(r'(?m)^\s*\*[^;\n]+?\s*=\s*[^;\n]+;',text[last_snapshot:dispatch]));self.assertEqual(len(publications),4)
        removed=publications[-1];begin=last_snapshot+removed.start();end=last_snapshot+removed.end()
        with self.assertRaises(ValueError):audit_staged((text[:begin]+text[end:]).encode(),good[1])
        changed=good[0].replace(b'__noinline__',b'')
        with self.assertRaises(ValueError):audit_staged(changed,good[1])
if __name__=='__main__':unittest.main()
