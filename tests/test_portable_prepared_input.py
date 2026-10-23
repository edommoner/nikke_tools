"""The GPU child may reuse validated bytes, never a CPU state/unchecked cache."""
import copy,importlib.util,json,struct,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('prepared_input_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)

class PreparedInputTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.capture=self.root/'capture';self.capture.mkdir()
  self.data=struct.pack('<II',1,7);self.domain={'amount':9}
  digest=lambda v:cli.sha(json.dumps(v,sort_keys=True).encode())
  self.m=dict(suite='fixture',package_id='owned',golden=dict(input_sha256=cli.sha(self.data),entries=[dict(name='native/one',input_sha256=cli.sha(self.data[4:]),native_sha256=digest(self.domain))]))
  def native(value):
   self.assertFalse((self.capture/'input.bin').exists(),'Publish only after native gate')
   return value
  self.adapter=types.SimpleNamespace(suite=types.SimpleNamespace(INPUT=1),cross=types.SimpleNamespace(digest=digest),native_reference=native)
  self.rows=[('native/one',[7],self.domain)]
 def publish(self):
  receipt=cli.publish_transport_input(self.m,self.capture,self.data,1)
  cli.write(self.capture/'cpu.json',dict(passed=True,input_count=1,input_sha256=cli.sha(self.data),gpu_calls=dict(build=0,execute=0),transport_input=receipt))
  return receipt
 def start(self):
  cli.write(self.capture/'start.json',{});cli.write(self.capture/'run.json',dict(input_protocol=cli.PREPARED_INPUT_PROTOCOL))
 def test_preflight_publishes_exact_input_only_after_all_native_comparisons(self):
  with patch.object(cli,'ROOT',self.root),patch.object(cli,'open_suite',return_value=self.adapter),patch.object(cli,'prepare_entries',return_value=(self.rows,self.data)):
   result=cli.cpu_preflight(self.m,input_capture=self.capture)
  self.assertEqual((self.capture/'input.bin').read_bytes(),self.data)
  cli.write(self.capture/'cpu.json',result)
  self.assertEqual(cli.read_prepared_transport_input(self.m,self.capture),(self.data,1))
  self.assertEqual(result['gpu_calls'],dict(build=0,execute=0));self.assertEqual(result['native_oracles'],1)
 def test_failed_native_gate_cannot_publish_input_or_receipt(self):
  self.adapter.native_reference=lambda _:dict(amount=10)
  with patch.object(cli,'ROOT',self.root),patch.object(cli,'open_suite',return_value=self.adapter),patch.object(cli,'prepare_entries',return_value=(self.rows,self.data)),self.assertRaisesRegex(ValueError,'CPU/input mismatch'):
   cli.cpu_preflight(self.m,input_capture=self.capture)
  self.assertFalse((self.capture/'input.bin').exists());self.assertFalse((self.capture/'input-preflight.json').exists())
 def test_child_passes_verified_bytes_without_importing_or_repacking_adapter(self):
  import portable_backend
  self.publish();self.start();calls=[]
  def transport(source,entry,data,input_words,output_words,backend,*,readback_path):
   calls.append((data,input_words,output_words));readback_path.write_bytes(b'saved');return None,dict(transport='fixture')
  with patch.object(cli,'verify_package',return_value=self.m),patch.dict(cli.SUITES,fixture=dict(source='unused.slang')),patch.object(cli,'open_suite',side_effect=AssertionError('Adapter import forbidden')),patch.object(cli,'prepare_entries',side_effect=AssertionError('Repacking forbidden')),patch.object(cli,'copy_generated'),patch.object(portable_backend,'execute',side_effect=transport):
   cli.child(self.capture,'metal')
  self.assertEqual(calls,[(self.data,1,786432)])
  stages=[json.loads(line)['stage'] for line in (self.capture/'preparation.jsonl').read_text().splitlines()]
  self.assertIn('gpu_child_prepared_input',stages);self.assertNotIn('gpu_child_legacy_input',stages)
 def test_same_size_byte_change_fails_without_fallback(self):
  self.publish();(self.capture/'input.bin').write_bytes(struct.pack('<II',1,8))
  with patch.object(cli,'open_suite',side_effect=AssertionError('No fallback')),self.assertRaisesRegex(ValueError,'differs from golden'):
   cli.read_prepared_transport_input(self.m,self.capture)
 def test_receipt_cannot_change_package_framing_schema_or_add_fields(self):
  receipt=self.publish()
  for key,value in [('schema',True),('package_id','foreign'),('input_words',2),('input_count',2),('input_bytes',0),('extra','ignored')]:
   changed=dict(receipt,**{key:value});cli.write(self.capture/'input-preflight.json',changed)
   with self.subTest(key=key),self.assertRaises(ValueError):cli.read_prepared_transport_input(self.m,self.capture)
 def test_failed_or_forged_gate_is_rejected(self):
  self.publish();original=cli.load(self.capture/'cpu.json')
  for change in [dict(passed=False),dict(input_count=True),dict(gpu_calls=dict(build=False,execute=0)),dict(gpu_calls=dict(build=1,execute=0)),dict(transport_input={})]:
   cli.write(self.capture/'cpu.json',dict(original,**change))
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'CPU gate mismatch'):cli.read_prepared_transport_input(self.m,self.capture)
 def test_missing_prepared_file_stops_child_without_legacy_repack(self):
  self.publish();self.start();(self.capture/'input-preflight.json').unlink()
  with patch.object(cli,'verify_package',return_value=self.m),patch.object(cli,'prepare_legacy_child_input',side_effect=AssertionError('No fallback')),self.assertRaisesRegex(ValueError,'missing or linked'):
   cli.child(self.capture,'metal')
 def test_existing_files_cannot_be_replaced(self):
  self.publish();before=(self.capture/'input.bin').read_bytes()
  with self.assertRaisesRegex(ValueError,'Fresh prepared'):cli.publish_transport_input(self.m,self.capture,self.data,1)
  self.assertEqual((self.capture/'input.bin').read_bytes(),before)
 def test_independent_audit_rechecks_prepared_bytes_even_without_artifact_inventory(self):
  self.publish();cli.write(self.capture/'run.json',dict(package_id=self.m['package_id'],mode='gpu',input_protocol=cli.PREPARED_INPUT_PROTOCOL))
  (self.capture/'input.bin').write_bytes(struct.pack('<II',1,8))
  with patch.object(cli,'verify_package',return_value=self.m),self.assertRaisesRegex(ValueError,'differs from golden'):
   cli.audit_capture(self.capture,verify_artifacts=False)
 def test_global_digest_cannot_hide_bad_row_digest_or_count(self):
  bad=copy.deepcopy(self.m);bad['golden']['entries'][0]['input_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'row differs'):cli.publish_transport_input(bad,self.capture,self.data,1)
  bad=copy.deepcopy(self.m);data=struct.pack('<II',2,7);bad['golden']['input_sha256']=cli.sha(data)
  with self.assertRaisesRegex(ValueError,'framing'):cli.publish_transport_input(bad,self.capture,data,1)
  self.assertFalse((self.capture/'input.bin').exists())
if __name__=='__main__':unittest.main()
