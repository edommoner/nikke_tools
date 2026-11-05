"""The bounded device check cannot substitute for full106 certification."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('frame_device_test',ROOT/'research/verify-resident-frames-device-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ResidentFrameDeviceTests(unittest.TestCase):
 def test_prefix_and_all_comparison_providers_are_shared_existing_functions(self):
  self.assertIs(a.prepare,a.prefix.prepare)
  for name in ('native_reference','compare','native_comparison_adapter','validate_rejection'):
   self.assertIs(getattr(a,name),getattr(a.full,name))
  self.assertIs(a.NATIVE_COMPARISON_CONTEXT,a.full.NATIVE_COMPARISON_CONTEXT)

if __name__=='__main__':unittest.main()
