"""Catch cross-language admission drift before native work or device access."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_wire_layout as wire
ROOT=Path(__file__).resolve().parents[1]

class WireLayoutTests(unittest.TestCase):
 def test_new_composed_entry_requires_the_complete_explicit_wire(self):
  import portable_backend
  source='gpu/world_original_lock_health_parts_entry.slang'
  portable_backend.validate_composed_stride(source,109536,1310720)
  for name,iw,ow in [(source,109535,1310720),(source,109536,1310719),('gpu/unregistered_health_entry.slang',109536,1310720)]:
   with self.subTest(name=name,iw=iw,ow=ow),self.assertRaises(ValueError):portable_backend.validate_composed_stride(name,iw,ow)
 def test_current_swift_and_python_have_the_same_limits(self):
  self.assertTrue(wire.check_metal(ROOT,2064786)['passed'])
  import portable_backend
  self.assertEqual((portable_backend.MAX_INPUT_WORDS,portable_backend.MAX_OUTPUT_WORDS),(wire.MAX_INPUT_WORDS,wire.MAX_OUTPUT_WORDS))
 def test_missing_new_width_fails_before_device_work(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'scripts').mkdir();(root/'scripts/run-metal-probe.swift').write_text(wire.metal_guard(wire.LARGE_OUTPUT_WORDS[:-1])+'\n')
   with self.assertRaisesRegex(ValueError,'admission differs'):wire.check_metal(root,2064786)
 def test_arbitrary_caps_duplicate_guards_and_unregistered_widths_fail(self):
  for text in [wire.metal_guard().replace('131072','131073'),wire.metal_guard()+'\n'+wire.metal_guard()]:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);(root/'scripts').mkdir();(root/'scripts/run-metal-probe.swift').write_text(text+'\n')
    with self.assertRaises(ValueError):wire.check_metal(root)
  for value in [0,True,2064785,2064787]:
   with self.subTest(value=value),self.assertRaises(ValueError):wire.check_metal(ROOT,value)
 def test_every_registered_large_width_is_accepted(self):
  for value in wire.LARGE_OUTPUT_WORDS:self.assertEqual(wire.check_metal(ROOT,value)['selected_output_words'],value)

if __name__=='__main__':unittest.main()
