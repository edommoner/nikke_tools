"""Raw IEEE bits, capacity and existing initialization survive frame storage."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import portable_dispatch_frames as frames
s=importlib.util.spec_from_file_location('frame_probe_test',ROOT/'research/verify-dispatch-frame-storage-short.py');probe=importlib.util.module_from_spec(s);s.loader.exec_module(probe)

class DispatchFrameStorageTests(unittest.TestCase):
 def test_recertified_full106_retains_every_old_result_and_binds_current_source_certificate(self):
  import json,hashlib
  sys.path.insert(0,str(ROOT/'scripts'));import nikke_gpu
  from portable_backend import source_hashes
  suite=nikke_gpu.SUITES['coordinate-resident-frames']
  old=json.loads((ROOT/'research/portable-coordinate-resident-frames-short-expected.json').read_text())
  raw=(ROOT/suite['golden']).read_bytes();new=json.loads(raw)
  for field in ('entries','input_sha256','output_sha256'):self.assertEqual(old[field],new[field])
  self.assertEqual(len(new['entries']),106)
  self.assertEqual(new['source_sha256'],source_hashes(suite['source']))
  diagnostic=nikke_gpu.SUITES[nikke_gpu.compiler_alias('coordinate-resident-frames')]
  cert=json.loads((ROOT/diagnostic['golden']).read_text())
  self.assertEqual(cert['source_sha256'],new['source_sha256'])
  self.assertEqual(cert['generated_normalized'],new['generated_normalized'])
  self.assertEqual(cert['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
  self.assertFalse(cert['calculation_verified']);self.assertFalse(cert['executable_battle_verified'])

 def test_historical_inverse_accepts_only_reviewed_sources_and_retains_all_old_baselines(self):
  from portable_dispatch_frame_source_contract import ledger,project_sources
  data=ledger(ROOT);old=project_sources(ROOT)
  for name,row in data['sources'].items():
   self.assertEqual(old[name],row['baseline'])
   with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'Unreviewed dispatch frame source'):
    project_sources(ROOT,{name:row['current']+'\n// mutated'})
  for name in data['added_sources']:
   with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'Unreviewed dispatch frame dependency'):
    project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// mutated'})
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
 def test_full106_profile_keeps_the_same_inputs_and_whole_tail_comparator(self):
  sys.path.insert(0,str(ROOT/'scripts'));import nikke_gpu
  old=nikke_gpu.SUITES['coordinate-resident-arc'];new=nikke_gpu.SUITES['coordinate-resident-frames']
  for key in ('inputs','native','output_words'):self.assertEqual(old[key],new[key])
  s=importlib.util.spec_from_file_location('full_frame_test',ROOT/new['script']);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
  for name in ('prepare','compare','native_reference','native_comparison_adapter','validate_rejection'):self.assertIs(getattr(a,name),getattr(a.parent,name))
  self.assertEqual((new['inputs'],new['native']),(106,63));self.assertFalse(new['development_only'])
  self.assertNotEqual(old['source'],new['source']);self.assertNotEqual(old['golden'],new['golden'])
  from portable_package_projection import SUPPORTED_SUITES
  self.assertIn('compiler-full--coordinate-resident-frames',SUPPORTED_SUITES);self.assertIn('coordinate-resident-frames',SUPPORTED_SUITES)
  from portable_package_projection import roots_for
  roots=roots_for(new,nikke_gpu.SMOKE_TESTS)
  self.assertIn(new['script'],roots);self.assertIn('tests/test_dispatch_frame_storage.py',roots)
  self.assertIn('tests/test_portable_staged_preflight.py',roots)

if __name__=='__main__':unittest.main()
