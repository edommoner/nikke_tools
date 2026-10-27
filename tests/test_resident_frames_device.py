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
 def test_short_scope_keeps_full_source_wire_and_all_full106_cases_registered(self):
  import nikke_gpu as cli
  full=cli.SUITES['coordinate-resident-frames'];short=cli.SUITES['resident-frames-device']
  self.assertEqual((full['inputs'],full['native']),(106,63));self.assertFalse(full['development_only'])
  self.assertEqual((short['inputs'],short['native']),(4,4));self.assertFalse(short['development_only'])
  self.assertEqual(short['source'],full['source']);self.assertEqual(short['output_words'],full['output_words'])
  self.assertNotEqual(short['golden'],full['golden'])
  self.assertTrue(set(cli.SUITES['coordinate-resident-device']['tests'])<=set(short['tests']))
  self.assertIn('test_dispatch_frame_storage.py',short['tests'])
  from portable_package_projection import SUPPORTED_SUITES
  self.assertIn('resident-frames-device',SUPPORTED_SUITES);self.assertNotIn('coordinate-resident-frames',SUPPORTED_SUITES)

if __name__=='__main__':unittest.main()
