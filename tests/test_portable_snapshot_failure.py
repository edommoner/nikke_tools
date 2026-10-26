"""Process-snapshot failures remain fail-closed with redacted diagnostics."""
import json,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/folder) for folder in ('app','research')]
import windows_validation_observer as observer

class SnapshotFailureTests(unittest.TestCase):
 def result(self,code,data):return subprocess.CompletedProcess([],code,stdout=json.dumps(data),stderr='SECRET command lines')
 def test_valid_snapshot_shape_retained(self):
  data=dict(rows=[],listeners=[]);self.assertEqual(observer.snapshot_data(self.result(0,data)),data)
 def test_native_failure_records_stage_and_numeric_codes(self):
  for stage in ['setup','processes','listeners','serialize']:
   with self.subTest(stage=stage),self.assertRaisesRegex(RuntimeError,'stage='+stage+', category=13, hresult=-2146233087'):
    observer.snapshot_data(self.result(1,dict(snapshot_error=dict(stage=stage,category=13,hresult=-2146233087))))
 def test_failure_never_returns_partial_rows_or_command_lines(self):
  data=dict(rows=[dict(CommandLine='SECRET')],listeners=[],snapshot_error=dict(stage='processes',category=1,hresult=2,message='SECRET'))
  try:observer.snapshot_data(self.result(1,data))
  except RuntimeError as error:
   self.assertNotIn('SECRET',str(error));self.assertNotIn('CommandLine',str(error))
  else:self.fail('Snapshot failure accepted')
 def test_invalid_failure_metadata_is_not_echoed(self):
  data=dict(snapshot_error=dict(stage='SECRET',category='SECRET',hresult=True))
  with self.assertRaisesRegex(RuntimeError,'stage=unknown, category=None, hresult=None'):observer.snapshot_data(self.result(1,data))
 def test_startup_or_non_json_failure_stays_closed(self):
  result=self.result(19,{});result.stdout='SECRET'
  with self.assertRaisesRegex(RuntimeError,'exit=19, stage=unknown'):observer.snapshot_data(result)
 def test_zero_exit_cannot_hide_error_or_invalid_snapshot(self):
  for data in [None,[],{},dict(rows={},listeners=[]),dict(rows=[],listeners=None),dict(rows=[],listeners=[],snapshot_error={})]:
   with self.subTest(data=data),self.assertRaisesRegex(RuntimeError,'Invalid process snapshot'):observer.snapshot_data(self.result(0,data))
 def test_query_contains_no_fallback_retry_or_weakened_error_policy(self):
  result=self.result(1,dict(snapshot_error=dict(stage='listeners',category=13,hresult=1)))
  with patch.object(observer,'os',types.SimpleNamespace(name='nt')),patch.object(observer.subprocess,'run',return_value=result) as run:
   with self.assertRaises(RuntimeError):observer.capture_snapshot('C:/original','C:/validation')
  self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.kwargs['timeout'],20)
  script=run.call_args.args[0][-1]
  self.assertIn("$ErrorActionPreference='Stop'",script);self.assertNotIn('SilentlyContinue',script)
  self.assertIn('Get-CimInstance Win32_Process',script);self.assertIn('Get-NetTCPConnection -State Listen',script)
  self.assertNotIn('$_.Exception.Message',script);self.assertNotIn('$_.ScriptStackTrace',script)


class SnapshotDiagnosticTests(unittest.TestCase):
 def invoke(self,reader):
  import tempfile
  from portable_windows_snapshot import check
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);original=root/'original';validation=root/'validation';original.mkdir();validation.mkdir();out=validation/'report.json'
   result=check(original,validation,out,reader=reader);self.assertEqual(json.loads(out.read_text()),result)
   with self.assertRaises(FileExistsError):check(original,validation,out,reader=lambda *a:self.fail('Repeated query'))
   return result
 def test_failure_writes_fresh_report_without_private_exception_text(self):
  def read(*a):raise OSError('SECRET command lines')
  r=self.invoke(read);self.assertFalse(r['snapshot_verified']);self.assertNotIn('SECRET',json.dumps(r));self.assertEqual(r['gpu_calls'],0)
 def test_success_is_not_preservation_or_calculation(self):
  r=self.invoke(lambda *a:dict(service_status='unverified',command_lines_saved=False))
  self.assertTrue(r['snapshot_verified']);self.assertIsNone(r['preservation_verified']);self.assertFalse(r['calculation_verified'])
 def test_timeout_does_not_serialize_command_script(self):
  def read(*a):raise subprocess.TimeoutExpired(['SECRET'],20,output='SECRET',stderr='SECRET')
  r=self.invoke(read);self.assertEqual(r['error']['timeout_seconds'],20);self.assertNotIn('SECRET',json.dumps(r))
 def test_known_structured_failure_is_preserved(self):
  def read(*a):raise RuntimeError('Windows process snapshot unavailable (exit=1, stage=listeners, category=13, hresult=-1); no command lines retained')
  self.assertIn('stage=listeners',self.invoke(read)['error']['message'])
 def test_shared_workspace_and_outside_report_are_rejected_before_query(self):
  import tempfile
  from portable_windows_snapshot import check
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);validation=root/'validation';validation.mkdir()
   with self.assertRaisesRegex(ValueError,'Separate'):check(root,validation,validation/'out.json',reader=lambda *a:self.fail())
   original=root/'original';original.mkdir()
   with self.assertRaisesRegex(ValueError,'inside'):check(original,validation,root/'outside.json',reader=lambda *a:self.fail())

if __name__=='__main__':unittest.main()
