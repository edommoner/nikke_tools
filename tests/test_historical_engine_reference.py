"""Historical evidence selection is explicit, hash-bound and CPU-only."""
import os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class HistoricalReferenceTests(unittest.TestCase):
 def child(self,body):
  code="import sys;sys.path[:0]=['tests','app','research'];"+body
  result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
 def test_historical_selection_keeps_production_default_current(self):
  self.child("import engine_worker as w;assert w.ENGINE.name=='nikke-calc-master';assert w.REVISION.startswith('67835ca3')")
  self.child("import historical_engine_reference as h;w=h.install();assert w.ENGINE.name=='nikke-calc-23164e4';assert w.REVISION==h.OLD_REVISION")
 def test_changed_historical_calculation_bytes_are_refused(self):
  self.child("""\nfrom pathlib import Path
from unittest.mock import patch
import historical_engine_reference as h
original=Path.read_bytes
def corrupt(path):return b'changed' if path.name=='timeline.py' else original(path)
with patch.object(Path,'read_bytes',corrupt):
 try:h.install()
 except ValueError as error:assert 'Historical reference bytes changed' in str(error)
 else:raise AssertionError('Changed historical calculation admitted')
""")
 def test_historical_selection_forbids_unmocked_device_execution(self):
  self.child("""\nimport historical_engine_reference as h
h.install()
import portable_backend
for call in (portable_backend.execute,portable_backend.execute_batches):
 try:call()
 except RuntimeError as error:assert 'Device execution forbidden' in str(error)
 else:raise AssertionError('Historical reference admitted device execution')
""")
if __name__=='__main__':unittest.main()
