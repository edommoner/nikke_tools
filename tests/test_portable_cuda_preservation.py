"""Fault injection: a complete calculation cannot hide process preservation failure."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
import portable_typed_cuda_proof_audit as proof


class PreservationProof(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);(self.root/'research').mkdir()
  self.blobs={'gpu/fixture.slang':b'fixed calculation source'}
  digest=lambda b:hashlib.sha256(b).hexdigest()
  self.golden=dict(input_sha256='input',output_sha256='output',entries=[dict(name='native/fixture',native_sha256='native')],generated_normalized={'cuda':'cu','metal':'msl'},source_sha256={'gpu/fixture.slang':digest(self.blobs['gpu/fixture.slang'])})
  self.blobs['research/fixture-golden.json']=json.dumps(self.golden).encode()
  evidence=dict(backend='cuda',gpu_execution_verified=True,input_sha256='input',output_sha256='output',source_sha256=self.golden['source_sha256'],transport=dict(cases=1))
  self.summary=dict(passed=True,input_count=1,input_sha256='input',output_sha256='output',entries=self.golden['entries'],generated_normalized=self.golden['generated_normalized'],evidence=evidence)
  flags={k:True for k in ('nvrtc_compile_returned_success','cuda_launch_returned_success','cuda_synchronize_returned_success','cuda_readback_returned_success')}
  self.execution=dict(passed=True,timed_out=False,child_exit_code=0,final_child_exit_code=0,error=None,cleanup_error=None,below_normal_priority=True,timeout_seconds=180,cleanup_wait_seconds=5,elapsed_seconds=1,gpu_retry_count=0,phase=dict(events=50,**flags))
  rows=[]
  for stage in ('nvrtcCompileProgram','cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2'):
   rows.extend([dict(stage=stage,state='entered'),dict(stage=stage,state='returned',return_code=0)])
  rows.extend(dict(stage='other',state='returned') for _ in range(41));rows.append(dict(stage='fixture_suite',state='returned'))
  for i,row in enumerate(rows):row['monotonic_ns']=i
  cpu=dict(passed=True,input_count=1,native_oracles=1,input_sha256='input',source_sha256=self.golden['source_sha256'],gpu_calls=dict(build=0,execute=0))
  pre=dict(source_commit='fixture',passed=True,cpu_short=dict(exit_code=0),original_head_before='61a43e91301841c272badce519e4d8984bb5efae',cpu_short_report=cpu,cpu_tests=[dict(pattern='fixture-test.py',expected_count=1,exit_code=0,stderr='Ran 1 tests\n\nOK\n')])
  self.receipt=dict(source_commit='fixture',passed=True,original_head_equal=True,original_status_equal=True,existing_gpu_service_preserved=False,residual_verification_process_count=0,actual_gpu_execution_count=1,gpu_retry_count=0,cpu_preflight=pre,phase_rows=rows)
  self.payload=dict(source_commit='fixture',file_count=1,files=[dict(path='gpu/fixture.slang',bytes=len(self.blobs['gpu/fixture.slang']),sha256=digest(self.blobs['gpu/fixture.slang']))])
  self.kw=dict(version=999,source='fixture',expected_file='fixture-golden.json',inputs=1,native_oracles=1,test_counts=[('fixture-test.py',1)],phase_suite='fixture_suite',old_replays=[],payload_files=1,payload_bytes=len(self.blobs['gpu/fixture.slang']))
 def run_proof(self,diagnostic=False):
  files={'windows-portable-world-v999-summary.json':self.summary,'portable-world-v999-execution.json':self.execution,'portable-cross-v999-receipt.json':self.receipt}
  artifacts=[]
  for name,value in files.items():
   data=json.dumps(value).encode();(self.root/'research'/name).write_bytes(data);artifacts.append(dict(local_name=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
  for name,value in [('fixture-golden.json',self.golden),('portable-cross-v999-import-receipt.json',dict(source_commit='fixture',artifacts=artifacts)),('portable-world-v999-source-payload.json',self.payload)]:
   (self.root/'research'/name).write_text(json.dumps(value))
  def blob(command,**kwargs):
   self.assertEqual(command[:2],['git','show']);return self.blobs[command[2].removeprefix('fixture:')]
  with patch.object(proof,'ROOT',self.root),patch.object(proof.subprocess,'check_output',side_effect=blob):return proof.audit(**self.kw,preservation_diagnostic=diagnostic)
 def test_scalar_cpu_call_receipt_requires_explicit_format_and_exact_integer_zero(self):
  self.receipt['cpu_preflight']['cpu_short_report']['gpu_calls']=0
  with self.assertRaises(AssertionError):self.run_proof(True)
  self.kw['cpu_gpu_calls_format']='scalar'
  self.assertTrue(self.run_proof(True)['calculation_verified'])
  for value in (False,1,None,{'build':0,'execute':0}):
   self.receipt['cpu_preflight']['cpu_short_report']['gpu_calls']=value
   with self.subTest(value=value),self.assertRaises(AssertionError):self.run_proof(True)
 def test_unknown_cpu_call_receipt_format_rejected(self):
  self.kw['cpu_gpu_calls_format']='guess'
  with self.assertRaises(ValueError):self.run_proof(True)
 def test_strict_audit_rejects_calculation_success_with_missing_processes(self):
  with self.assertRaises(AssertionError):self.run_proof()
 def test_diagnostic_keeps_overall_failure_and_reports_calculation_separately(self):
  result=self.run_proof(True);self.assertFalse(result['passed']);self.assertFalse(result['original_windows_work_and_service_preserved']);self.assertFalse(result['preservation_verified']);self.assertTrue(result['calculation_verified']);self.assertTrue(result['preservation_findings'])
 def test_diagnostic_still_rejects_failed_cuda_synchronize(self):
  row=next(r for r in self.receipt['phase_rows'] if r['stage']=='cuCtxSynchronize' and r['state']=='returned');row['return_code']=700
  with self.assertRaises(AssertionError):self.run_proof(True)
 def test_strict_preserved_execution_passes_without_diagnostic_exception(self):
  self.receipt['existing_gpu_service_preserved']=True;result=self.run_proof();self.assertTrue(result['passed']);self.assertTrue(result['original_windows_work_and_service_preserved']);self.assertNotIn('calculation_verified',result)

 def missing_summary_counter(self,count):
  self.kw.update(old_replays=['old958'],single_suite_command='python fixture.py',summary_omission_counts={'old958':958});self.receipt['old958_execution_count']=count;self.receipt['bounded_driver']=dict(shared_gpu_command='python fixture.py')
 def test_omitted_summary_counter_needs_explicit_zero_receipt_and_fixed_dispatch(self):
  self.missing_summary_counter(0);r=self.run_proof(True);self.assertFalse(r['passed']);self.assertTrue(r['calculation_verified']);self.assertEqual(r['old958_reexecutions'],0);self.assertEqual(r['summary_omissions_verified_from_receipt_and_frozen_dispatch'],['old958'])
 def test_omitted_summary_counter_cannot_hide_a_recorded_reexecution(self):
  self.missing_summary_counter(1)
  with self.assertRaises(AssertionError):self.run_proof(True)
if __name__=='__main__':unittest.main()
