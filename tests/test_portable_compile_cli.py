"""Compiler-only orchestration cannot become a CUDA calculation proof."""
import ctypes as C
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
s=importlib.util.spec_from_file_location('compile_cli_test',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
import portable_backend as backend
from portable_phase_audit import Journal,NativeLibrary
from test_portable_cuda_artifact import NVRTC


class CompileCLITests(unittest.TestCase):
    def test_plan_binds_two_thread_options_and_rejects_unbounded_setting(self):
        normal=dict(package_id='plan-fixture',suite='coordinate-resident-arc',purpose='sealed')
        with patch.object(cli,'verify_package',return_value=normal),patch.object(cli.subprocess,'run',side_effect=AssertionError('No process')),patch.object(backend,'compile_cuda_source',side_effect=AssertionError('No compiler')):
            with patch.dict(os.environ,{'NIKKE_CUDA_SPLIT_COMPILE':'2'}):
                result=cli.compile_plan(self.root/'parallel-plan.json','ptx',None,2048,60)
                self.assertTrue(result['passed']);self.assertIn('--split-compile=2',result['compiler_options'])
                self.assertIn('--fmad=false',result['compiler_options']);self.assertFalse(result['claim_created'])
            with patch.dict(os.environ,{'NIKKE_CUDA_SPLIT_COMPILE':'0'}):
                result=cli.compile_plan(self.root/'unbounded-plan.json','ptx',None,2048,60)
                self.assertFalse(result['passed']);self.assertIsNone(result['compiler_options'])
                self.assertFalse(result['claim_created']);self.assertTrue(result['execution_claim_available'])

    def test_compile_plan_uses_diagnostic_policy_without_compiler_or_process(self):
        normal=dict(package_id='plan-fixture',suite='coordinate-resident-arc',purpose='sealed')
        with patch.object(cli,'verify_package',return_value=normal),patch.object(cli.subprocess,'run',side_effect=AssertionError('No process')),patch.object(backend,'compile_cuda_source',side_effect=AssertionError('No compiler')):
            result=cli.compile_plan(self.root/'normal-plan.json','cubin',1,2048,60)
            self.assertTrue(result['passed']);self.assertFalse(result['claim_created']);self.assertEqual(result['gpu_calls'],0)
            with self.assertRaises(FileExistsError):cli.compile_plan(self.root/'normal-plan.json','cubin',1,2048,60)
            normal.update(suite='compiler-full--coordinate-resident-arc',purpose='compiler-diagnostic')
            result=cli.compile_plan(self.root/'incompatible.json','cubin',1,2048,60)
            self.assertFalse(result['passed']);self.assertIn('PTX',result['error'])
            result=cli.compile_plan(self.root/'ptx.json','ptx',None,2048,60)
            self.assertTrue(result['passed'])
        self.assertFalse((self.root/'compile-claimed-cuda.json').exists())

    def test_preview_parent_child_audit_keep_the_same_ptx_diagnostic_invariant(self):
        diagnostic=dict(suite='compiler-full--coordinate-resident-arc')
        for stage in ('parent','child','audit'):
            cli.compiler_diagnostic_policy(diagnostic,'ptx',None,2048,stage)
            for kind,level,memory in [('cubin',1,2048),('ptx',1,2048),('ptx',None,1024)]:
                with self.subTest(stage=stage,kind=kind,level=level,memory=memory),self.assertRaisesRegex(ValueError,'PTX'):
                    cli.compiler_diagnostic_policy(diagnostic,kind,level,memory,stage)

    def test_plan_rejects_consumed_claim_even_when_artifact_changes(self):
        normal=dict(package_id='plan-fixture',suite='coordinate-resident-arc',purpose='sealed')
        claim=self.root/'compile-claimed-cuda.json'
        original=b'{"artifact_kind":"cubin","capture":"preserved-failure"}\n'
        claim.write_bytes(original)
        with patch.object(cli,'ROOT',self.root),patch.object(cli,'verify_package',return_value=normal),patch.object(cli,'run_job',side_effect=AssertionError('No execution')):
            for kind,level in [('cubin',1),('ptx',None)]:
                result=cli.compile_plan(self.root/(kind+'-consumed.json'),kind,level,2048,60)
                self.assertFalse(result['passed']);self.assertFalse(result['execution_claim_available'])
                self.assertIn('already consumed',result['error']);self.assertFalse(result['claim_created'])
                self.assertEqual(claim.read_bytes(),original)
            claim.unlink()
            result=cli.compile_plan(self.root/'fresh-plan.json','ptx',None,2048,60)
            self.assertTrue(result['passed']);self.assertTrue(result['execution_claim_available'])
            self.assertFalse(claim.exists())

    @unittest.skipIf(os.name=='nt','Creating symlinks requires unrelated Windows privileges')
    def test_plan_rejects_dangling_claim_without_following_or_removing_it(self):
        normal=dict(package_id='plan-fixture',suite='coordinate-resident-arc',purpose='sealed')
        claim=self.root/'compile-claimed-cuda.json';claim.symlink_to(self.root/'missing-target')
        with patch.object(cli,'ROOT',self.root),patch.object(cli,'verify_package',return_value=normal):
            result=cli.compile_plan(self.root/'linked-claim.json','ptx',None,2048,60)
        self.assertFalse(result['passed']);self.assertFalse(result['execution_claim_available'])
        self.assertTrue(claim.is_symlink());self.assertFalse(claim.exists())

    def test_plan_rejects_development_and_invalid_budgets_before_execution(self):
        normal=dict(package_id='plan-fixture',suite='coordinate-resident-arc',purpose='sealed')
        with patch.object(cli,'verify_package',return_value=normal):
            for index,(memory,timeout) in enumerate([(2048,61),(2048,0),(4097,60),(True,60),(2048,True)]):
                self.assertFalse(cli.compile_plan(self.root/f'budget-{index}.json','cubin',1,memory,timeout)['passed'])
            normal['purpose']='development'
            self.assertFalse(cli.compile_plan(self.root/'development.json','cubin',1,2048,60)['passed'])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.capture=self.root/'capture';self.capture.mkdir()
        self.cuda=self.root/'generated.cu';self.cuda.write_bytes(b'cuda')
        self.metal=self.root/'generated.metal';self.metal.write_bytes(b'metal')
        self.dll=self.root/'nvrtc64_dummy.dll';self.dll.write_bytes(b'compiler')
        self.m=dict(package_id='compiler-fixture',suite='readiness',purpose='sealed',
            golden=dict(source_sha256={},generated_normalized=dict(cuda=cli.sha(b'cuda'),metal=cli.sha(b'metal'))))
        self.native=NVRTC();self.journal=Journal(self.capture/'phases.jsonl')
        self.loader=Mock(return_value=NativeLibrary(self.native,self.journal))

    def fake_compile(self,source):
        lib=backend.C.WinDLL('nvrtc64_dummy.dll')
        artifact,receipt=backend.compile_cuda_artifact(lib,source.read_bytes(),[self.dll],artifact_kind='cubin')
        source.with_suffix('.cubin').write_bytes(artifact)
        return artifact,receipt

    def copied(self,capture,suite):
        for source,name in [(self.cuda,'generated.cu'),(self.metal,'generated.metal'),(self.cuda.with_suffix('.cubin'),'compiled.cubin')]:
            (capture/name).write_bytes(source.read_bytes())

    def context(self,compile_source=None):
        import contextlib
        stack=contextlib.ExitStack()
        stack.enter_context(patch.object(backend.C,'WinDLL',self.loader,create=True))
        stack.enter_context(patch.object(backend,'build',return_value=({'cuda':self.cuda,'metal':self.metal},{})))
        stack.enter_context(patch.object(backend,'compile_cuda_source',compile_source or self.fake_compile))
        stack.enter_context(patch.object(cli,'copy_generated',self.copied))
        stack.enter_context(patch.object(cli,'module',return_value=types.SimpleNamespace(normalized=cli.sha)))
        stack.enter_context(patch.dict(os.environ,{'NIKKE_CUDA_CACHE_REQUIRED':'0','NIKKE_CUDA_PTXAS_OPT_LEVEL':'','NIKKE_CUDA_COMPILE_CACHE':str(self.root/'cache')}))
        return stack

    def proof(self):
        with self.context():cli.compile_child(self.m,self.capture,'cuda')
        cli.write(self.capture/'run.json',dict(package_id=self.m['package_id'],backend='cuda',mode='compile-only',artifact_kind='cubin',ptxas_level=None,memory_limit_mb=2048))
        cli.write(self.capture/'execution.json',dict(passed=True,timeout_seconds=60,observation_error=None,wait_completed_unix_ns=time.time_ns()))
        pre=dict(child_pid=os.getpid(),child_ppid=17,job_members=[os.getpid()],child_creation_filetime_ticks='100',observed_unix_ns=1,job_memory_limit_bytes=2048*1024*1024)
        post=dict(pre,job_members=[],observed_unix_ns=time.time_ns())
        cli.write(self.capture/'job.json',dict(records=[dict(child_pid=os.getpid(),wrapper_pid=17,pre_gate_verified=True,inspection_error=None,pre_gate=pre,post_wait=post)]))

    def audit(self):
        with patch.object(cli,'module',return_value=types.SimpleNamespace(normalized=cli.sha)):
            return cli.audit_compile_capture(self.m,self.capture,verify_artifacts=False)

    def test_compiler_success_requires_job_and_stays_calculation_false(self):
        self.proof();r=self.audit()
        self.assertTrue(r['compiler_verified']);self.assertTrue(r['containment_verified'])
        self.assertFalse(r['calculation_verified']);self.assertFalse(r['preservation_verified']);self.assertFalse(r['passed'])
        self.assertEqual(r['gpu_calls'],0);self.loader.assert_called_once_with('nvrtc64_dummy.dll')
        self.assertEqual(self.native.calls.count('compile'),1)

    def test_driver_load_attempt_is_rejected_before_any_library_is_loaded(self):
        with self.context(lambda source:backend.C.WinDLL('nvcuda.dll')):
            with self.assertRaisesRegex(RuntimeError,'Only the NVRTC'):cli.compile_child(self.m,self.capture,'cuda')
        self.loader.assert_not_called();self.assertFalse((self.capture/'compiler.json').exists())

    def test_failed_compiler_library_load_is_not_reported_as_loaded(self):
        self.loader.side_effect=OSError('Dependency could not be loaded')
        with self.context(),self.assertRaisesRegex(OSError,'Dependency could not be loaded'):
            cli.compile_child(self.m,self.capture,'cuda')
        rows=[json.loads(line) for line in (self.capture/'phases.jsonl').read_text().splitlines()]
        libraries=[r for r in rows if r['stage']=='cuda_compiler_library']
        self.assertEqual([r['state'] for r in libraries],['entered','raised'])
        self.assertEqual(libraries[-1]['exception'],'OSError')
        self.assertEqual(self.native.calls,[]);self.assertFalse((self.capture/'compiler.json').exists())

    def test_codegen_drift_is_rejected_before_compiler(self):
        self.m['golden']['generated_normalized']['cuda']='changed'
        with self.context(),self.assertRaisesRegex(ValueError,'sealed Metal proof'):cli.compile_child(self.m,self.capture,'cuda')
        self.loader.assert_not_called()

    def test_timeout_or_unproven_memory_limit_cannot_be_success(self):
        self.proof()
        p=self.capture/'execution.json';facts=cli.load(p);facts['passed']=False;cli.write(p,facts)
        self.assertFalse(self.audit()['compiler_verified'])
        facts['passed']=True;cli.write(p,facts)
        job=cli.load(self.capture/'job.json');job['records'][0]['post_wait']['job_memory_limit_bytes']=None;cli.write(self.capture/'job.json',job)
        self.assertFalse(self.audit()['compiler_verified'])

    def test_truncated_phase_is_a_retained_failure_instead_of_a_successful_artifact(self):
        self.proof()
        with (self.capture/'phases.jsonl').open('a') as stream:stream.write('{"interrupted')
        result=self.audit();self.assertFalse(result['compiler_verified'])
        self.assertIn('incomplete',result['error'])
        self.assertTrue((self.capture/'compiled.cubin').exists())

    def test_artifact_corruption_and_unexpected_gpu_calls_are_detected(self):
        self.proof();p=self.capture/'compiled.cubin';original=p.read_bytes();p.write_bytes(b'changed')
        self.assertFalse(self.audit()['compiler_verified']);p.write_bytes(original)
        self.journal.invoke('cuLaunchKernel',lambda:0,native=True)
        r=self.audit();self.assertFalse(r['compiler_verified']);self.assertIsNone(r['gpu_calls'])

    def test_compile_budget_and_development_package_reject_before_capture_creation(self):
        destination=self.root/'must-not-exist'
        fake=types.SimpleNamespace(name='nt',environ={'NIKKE_CUDA_COMPILE_CACHE':'dedicated-cache'})
        with patch.object(cli,'os',fake):
            for timeout,memory in [(61,2048),(0,2048),(60,4097)]:
                with self.assertRaises(ValueError):cli.compile_capture(destination,timeout,Path('original'),memory_limit_mb=memory)
            with patch.object(cli,'verify_package',return_value=dict(purpose='development')):
                with self.assertRaisesRegex(ValueError,'sealed'):cli.compile_capture(destination,60,Path('original'))
        self.assertFalse(destination.exists())


if __name__=='__main__':unittest.main()
