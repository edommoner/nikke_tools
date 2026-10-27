"""Interrupted dispatch recovery must keep failure history and all audit gates."""
import copy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','tests','research')]
import portable_readback_recovery as recovery
import test_portable_object_recovery as objects
cli=objects.cli


class ReadbackRecoveryTests(unittest.TestCase):
    def setUp(self):
        f=objects.RecoveryTests();f.setUp();self.addCleanup(f.doCleanups)
        self.package=f.package.resolve();self.capture=f.capture.resolve();self.outer=f.outer.resolve();self.packet=f.packet
        self.output=(f.f.root/'readback-audit').resolve();self.manifest=copy.deepcopy(f.f.base.m)
        self.manifest.update(files=[]);self.manifest['golden']['output_sha256']=cli.sha(b'saved-gpu-output')
        self.digest=self.manifest['golden']['output_sha256']
        cli.write(self.capture/'run.json',dict(package_id=self.manifest['package_id'],mode='gpu',backend='cuda',status='preflight'))
        linked=(f.f.root/'linked-stage'/'proof').resolve();linked.mkdir(parents=True)
        request=dict(linked_package=str(f.f.base.source_package.resolve()),linked_capture=str(linked))
        plan=self.packet.recipe(self.manifest['package_id'],'gpu-linked','cuda',self.outer,f.f.root/'original',180,request)
        cli.write(self.outer/'recipe.json',plan)
        cli.write(self.capture/'linked-artifact-request.json',dict(package=request['linked_package'],capture=request['linked_capture']))
        for name,target in (('gpu-claimed-cuda.json',self.capture),('packet-stage-claimed-gpu-linked-cuda.json',self.outer)):
            cli.write(self.package/name,dict(package_id=self.manifest['package_id'],capture=str(target)))
        (self.capture/'readback.bin').write_bytes(b'saved-gpu-output')
        cli.write(self.capture/'cpu.json',dict(passed=True))
        cli.write(self.capture/'cpu-tests.json',[dict(pattern='test_saved.py',exit_code=0,tests=1,failures=0,errors=0)])
        self.audit=Mock(return_value=dict(calculation_verified=True,containment_verified=True,preservation_verified=False,passed=False))
        self.original=types.SimpleNamespace(**vars(cli));self.original.ROOT=self.package
        self.original.verify_package=Mock(return_value=self.manifest)
        self.original.is_development=lambda _:False;self.original.compiler_only=lambda _:False
        self.original.SUITES={self.manifest['suite']:dict(tests=['test_saved.py'])}
        self.original.audit_capture=self.audit
        self.original.module=lambda _:self.packet
        self.controller=types.SimpleNamespace(**vars(cli));self.controller.ROOT=ROOT
        self.controller.verify_package=Mock(return_value=self.manifest)
        self.controller.module=lambda _:self.original

    def recover(self,**kwargs):
        return recovery.recover(self.controller,self.package,self.capture,kwargs.get('output',self.output),kwargs.get('digest',self.digest))

    def test_fresh_original_auditor_separate_result_preserves_incomplete_capture(self):
        before=recovery.snapshot(cli,self.package,self.capture)
        result=self.recover()
        self.audit.assert_called_once_with(self.capture,verify_artifacts=False)
        self.assertTrue(result['calculation_verified']);self.assertTrue(result['containment_verified'])
        for key in ('passed','original_stage_verified','original_capture_modified','preservation_verified'):
            self.assertIs(result[key],False)
        self.assertEqual(result['gpu_calls'],0)
        self.assertEqual(before,recovery.snapshot(cli,self.package,self.capture))
        self.assertEqual(cli.load(self.capture/'run.json')['status'],'preflight')
        for name in (*recovery.MISSING,'comparison.json'):self.assertFalse((self.capture/name).exists())
        with self.assertRaises(FileExistsError):self.recover()

    def test_raw_corruption_or_wrong_external_digest_rejected_before_native_audit(self):
        for index,digest in enumerate(('0'*64,'invalid')):
            with self.subTest(digest=digest),self.assertRaises(ValueError):self.recover(digest=digest,output=self.output.with_name('bad'+str(index)))
        (self.capture/'readback.bin').write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError,'Readback differs'):self.recover()
        self.audit.assert_not_called()

    def test_nonterminal_or_failed_child_and_changed_claim_are_rejected(self):
        cases=[(self.outer/'execution.json','timed_out',False),
               (self.capture/'execution.json','passed',False),
               (self.capture/'execution.json','child_exit_code',1),
               (self.capture/'run.json','backend','metal'),
               (self.package/'gpu-claimed-cuda.json','capture',str(self.outer))]
        for index,(path,key,value) in enumerate(cases):
            old=path.read_bytes();data=cli.load(path);data[key]=value;cli.write(path,data)
            with self.subTest(key=key),self.assertRaises(ValueError):self.recover(output=self.output.with_name('bad'+str(index)))
            path.write_bytes(old)
        self.audit.assert_not_called()

    def test_prior_result_and_original_or_upstream_output_rejected(self):
        for root in (self.package,self.outer,self.capture,Path(cli.load(self.capture/'linked-artifact-request.json')['package'])):
            with self.assertRaisesRegex(ValueError,'outside original'):self.recover(output=root/'new')
        cli.write(self.capture/'artifacts.json',dict(files=[]))
        with self.assertRaisesRegex(ValueError,'does not replace'):self.recover()

    def test_incomplete_tests_and_native_preflight_cannot_be_recovered(self):
        for index,(name,value) in enumerate((('cpu-tests.json',[]),('cpu.json',dict(passed=False)))):
            path=self.capture/name;old=path.read_bytes();cli.write(path,value)
            with self.assertRaisesRegex(ValueError,'incomplete'):self.recover(output=self.output.with_name('bad'+str(index)))
            path.write_bytes(old)
        self.audit.assert_not_called()

    def test_evidence_mutation_during_audit_and_dependency_drift_rejected(self):
        self.audit.side_effect=lambda *a,**k:((self.capture/'late.log').write_bytes(b'changed') and self.audit.return_value)
        with self.assertRaisesRegex(ValueError,'changed during'):self.recover()
        self.assertFalse((self.output/'result.json').exists())
        bad=copy.deepcopy(self.manifest);bad['files']=[dict(path='app/portable_backend.py',sha256='wrong')]
        self.controller.verify_package.side_effect=[bad,self.manifest]
        with self.assertRaisesRegex(ValueError,'dependency changed'):self.recover(output=self.output.with_name('drift'))

    def test_wrapper_exact_request_and_proof_scope(self):
        request=dict(source_package=str(self.package),source_capture=str(self.capture),output_sha256=self.digest)
        plan=self.packet.recipe('id','recover-readback','cuda',self.output,'/original',180,request)
        self.assertEqual(self.packet.proof_arguments(plan),['recover-readback','--source-package',str(self.package),'--source-capture',str(self.capture),'--out',str(self.output/'proof'),'--output-sha256',self.digest])
        good=dict(mode='recover-readback-only',calculation_verified=True,containment_verified=True,preservation_verified=True,original_outer_timed_out=True,original_stage_verified=False,original_capture_modified=False,gpu_calls=0,driver_load_calls=0,native_tool_calls=0)
        self.assertTrue(self.packet.verified_readback(good))
        for key,value in (('gpu_calls',1),('gpu_calls',False),('original_stage_verified',True),('preservation_verified',False),('containment_verified',False)):
            self.assertFalse(self.packet.verified_readback(dict(good,**{key:value})))
        for value in (dict(request,extra='--gpu'),dict(request,output_sha256='bad')):
            with self.assertRaises(ValueError):self.packet.object_request('recover-readback',value)


if __name__=='__main__':unittest.main()
