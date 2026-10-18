import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('carrier_gpu_oracle',ROOT/'scripts/verify-lifecycle-carriers.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LifecycleCarrierGPUTests(unittest.TestCase):
 def test_existing_operations_and_parent_continuation_identity(self):
  from verification_session import VerificationSession
  guard=VerificationSession();before=guard.fingerprint();rows=m.verify('native');stable=before==guard.fingerprint()
  report=dict(passed=stable and len(rows)==8 and all(row['passed'] for row in rows),backend='native',source_stable=stable,cases=rows)
  (ROOT/'research/carrier-native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  self.assertTrue(stable);self.assertEqual(len(rows),8)
  self.assertTrue(all(row['passed'] for row in rows),json.dumps([r for r in rows if not r['passed']],ensure_ascii=True))

if __name__=='__main__':unittest.main()
