import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('base_copy_gpu_oracle',ROOT/'scripts/verify-base-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class BaseCopyGPUTests(unittest.TestCase):
 def test_common_copies_and_raw_squads(self):
  from verification_session import VerificationSession
  guard=VerificationSession();before=guard.fingerprint()
  rows=m.verify('native');stable=before==guard.fingerprint()
  report=dict(passed=stable and len(rows)==19 and all(row['passed'] for row in rows),backend='native',source_stable=stable,cases=rows,verification_entry='test_detail_base_copy',source_hash_guard='Full acceptance runner provides content hashes; this method additionally guards file stamps and reference bindings.')
  (ROOT/'research/base-copy-native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  self.assertTrue(stable);self.assertEqual(len(rows),19)
  self.assertTrue(all(row['passed'] for row in rows),json.dumps([row for row in rows if not row['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
