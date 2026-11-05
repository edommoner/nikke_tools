"""A relocation contract validates addresses, never excludes arbitrary words."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_resident_arc_retention as audit

def put(block,index,value):struct.pack_into('<I',block,index*4,value)
class ResidentArcRetentionTests(unittest.TestCase):
 def setUp(self):
  self.old=bytearray(audit.PREFIX*4);self.new=bytearray(audit.OUTPUT*4)
 def trace(self):
  for block in [self.old,self.new]:
   put(block,audit.TYPED,0x44425431);put(block,audit.TYPED+1,1);put(block,audit.POINTER+1,1);put(block,audit.RECORD,1)
  put(self.old,audit.POINTER,audit.PREFIX+audit.RECORD);put(self.new,audit.POINTER,audit.OUTPUT+audit.RECORD)
 def test_verbatim_prefix_and_full_zero_tail(self):self.assertIsNone(audit.compare_block(self.old,self.new,1))
 def test_only_actual_trace_record_address_is_relocated(self):
  self.trace();r=audit.compare_block(self.old,self.new,1);self.assertEqual(r['new_address']-r['old_address'],32786)
 def test_wrong_pointer_value_is_rejected(self):
  self.trace();put(self.new,audit.POINTER,audit.OUTPUT+audit.RECORD+1)
  with self.assertRaisesRegex(ValueError,'case bases'):audit.compare_block(self.old,self.new,1)
 def test_adjacent_and_semantic_bytes_are_not_ignored(self):
  self.trace();put(self.new,audit.POINTER-1,1)
  with self.assertRaisesRegex(ValueError,'Non-address'):audit.compare_block(self.old,self.new,1)
 def test_record_header_and_owner_must_match(self):
  self.trace()
  for block in [self.old,self.new]:put(block,audit.RECORD,2)
  with self.assertRaisesRegex(ValueError,'identity'):audit.compare_block(self.old,self.new,1)
 def test_forged_field_without_trace_ownership_is_rejected(self):
  self.trace()
  for block in [self.old,self.new]:put(block,audit.TYPED,0)
  with self.assertRaisesRegex(ValueError,'ownership'):audit.compare_block(self.old,self.new,1)
 def test_tail_and_dimensions_are_full_checks(self):
  self.new[-1]=1
  with self.assertRaisesRegex(ValueError,'tail'):audit.compare_block(self.old,self.new,1)
  with self.assertRaisesRegex(ValueError,'Complete'):audit.compare_block(self.old,self.new[:-1],1)
if __name__=='__main__':unittest.main()
