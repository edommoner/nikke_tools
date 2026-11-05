"""Raw IEEE bits, capacity and existing initialization survive frame storage."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import portable_dispatch_frames as frames
s=importlib.util.spec_from_file_location('frame_probe_test',ROOT/'research/verify-dispatch-frame-storage-short.py');probe=importlib.util.module_from_spec(s);s.loader.exec_module(probe)

class DispatchFrameStorageTests(unittest.TestCase):


 def test_full_frame_and_generated_storage_match_single_shared_definition(self):
  self.assertEqual(frames.check_frame_type(ROOT),dict(capacity=32,frame_words=32,storage_words=1024))
  self.assertEqual((ROOT/'gpu/dispatch_frame_storage.slang').read_text(),frames.schema())
  offsets=[]
  for _,at,typ,_ in frames.FIELDS:offsets.extend(range(at,at+(2 if typ=='uint64_t' else 1)))
  self.assertEqual(set(range(32))-set(offsets),{1,5});self.assertEqual(len(offsets),len(set(offsets)))
 def test_signed_argument_nan_payload_and_signed_zero_bits_are_not_float_converted(self):
  raw=frames.encode(dict(argument=-2147483648,notifyDealt=0xffffffffffffffff,value=0x7ff8000000000001,time=0x8000000000000000))
  self.assertEqual(raw[19],0x80000000);self.assertEqual(raw[2:4],[0xffffffff,0xffffffff]);self.assertEqual(raw[20:24],[1,0x7ff80000,0,0x80000000])
  value=frames.decode(raw);self.assertEqual(value['argument'],-2147483648);self.assertEqual(value['value'],0x7ff8000000000001)
 def test_outside_exact_scalar_ranges_or_incomplete_wire_is_rejected(self):
  for values in (dict(argument=1<<31),dict(argument=-(1<<31)-1),dict(cursor=-1),dict(value=1<<64),dict(value=True),dict(unknown=1)):
   with self.subTest(values=values),self.assertRaises(ValueError):frames.encode(values)
  for raw in ([0]*31,[0]*33,[False]*32,[-1]*32):
   with self.subTest(length=len(raw)),self.assertRaises(ValueError):frames.decode(raw)
 def test_probe_checks_all32_slots_and_every_output_word_including_guard_errors(self):
  rows,_=probe.prepare();self.assertEqual(len(rows),5)
  for _,words,domain in rows:
   self.assertEqual(len(words),40);expected=probe.native_reference(domain);self.assertEqual(len(expected),1040)
   self.assertEqual(probe.compare(expected,domain),expected)
   for at in (1,4,16,1039):
    bad=list(expected);bad[at]^=1
    with self.subTest(op=domain['op'],word=at),self.assertRaises(AssertionError):probe.compare(bad,domain)
  self.assertEqual([probe.native_reference(row[2])[2] for row in rows],[0,0,0,1,1])
 def test_common_initializer_and_old_array_variant_remain_available(self):
  from portable_runtime_layout import runtime_initializer
  self.assertEqual(runtime_initializer(),(ROOT/'gpu/runtime_init.slang').read_text())
  self.assertIn('#define DISPATCH_FRAMES(name) Frame name[32]',frames.schema())
  self.assertIn('if (depth == 31) { s.error = 1; return; }',(ROOT/'gpu/event_runtime.slang').read_text())

if __name__=='__main__':unittest.main()
