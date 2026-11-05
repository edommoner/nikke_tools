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

if __name__=='__main__':unittest.main()
