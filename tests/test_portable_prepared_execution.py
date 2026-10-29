"""Claimed child dataflow with synthetic receipts/driver returns, no real GPU."""
import json,os,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_prepared_execution as execution
import portable_admission_authority as authority
import portable_admission_snapshot as snap
import test_portable_admission_authority as fixture
from portable_phase_audit import Journal


class PreparedExecutionTests(unittest.TestCase):
    def setUp(self):
        f=fixture.AuthorityTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f;self.cli=f.cli
        a=f.authenticate();authority.claim(self.cli,a);self.authority=a
        self.capture=Path(f.f.binding['future_capture']);self.capture.mkdir();(self.capture/'start.json').write_text('{}')
        self.claim_sha=snap.digest((f.consumer/'gpu-claimed-cuda.json').read_bytes())
        self.manifest=self.cli.verify_package(f.consumer)
        self.run=dict(schema=execution.RUN_SCHEMA,input_protocol=authority.PROTOCOL,mode='snapshot-gpu',backend='cuda',package_id=self.manifest['package_id'],capture=str(self.capture),claim_sha256=self.claim_sha,authority_sha256=snap.digest((f.f.base/'authority/authority.json').read_bytes()),binding=f.f.binding)
        self.save('run.json',self.run)
        self.proxy=patch.object(execution,'is_windows',return_value=True);self.proxy.start();self.addCleanup(self.proxy.stop)
        self.cli.SUITES['authority-fixture']['output_words']=1
        self.source=f.f.base/'runtime.cu';self.source.write_bytes(f.f.cuda);self.gpu_calls=0;self.emit_trace=True
    def save(self,name,value):(self.capture/name).write_text(json.dumps(value))
    def ownership(self):return execution.ownership(self.cli,self.manifest,self.capture,self.claim_sha)
    def cpu_execute(self,source,entry,packed,words,output_words,backend,*,readback_path):
        import portable_backend
        self.gpu_calls+=1
        image,receipt=portable_backend.compile_cuda_source(self.source,artifact_kind='cubin')
        self.assertEqual(image,self.f.f.image);self.assertEqual(packed,self.f.f.input)
        data=struct.pack('<I',123);Path(readback_path).write_bytes(data)
        j=Journal(self.capture/'phases.jsonl')
        if self.emit_trace:
            j.emit('cuMemsetD8_v2','entered',destination_device=9,value=0,byte_count=4);j.emit('cuMemsetD8_v2','returned',return_code=0)
            for name in ('cuLaunchKernel','cuCtxSynchronize'):
                j.emit(name,'entered');j.emit(name,'returned',return_code=0)
            j.emit('cuda_readback_file','entered',device_address=9,output_bytes=4,chunk_bytes=portable_backend.READBACK_CHUNK_BYTES)
            j.emit('cuMemcpyDtoH_v2','entered',source_device=9,byte_count=4);j.emit('cuMemcpyDtoH_v2','returned',return_code=0)
            j.emit('cuda_readback_file','returned',receipt=dict(output_bytes=4,chunk_bytes=portable_backend.READBACK_CHUNK_BYTES,chunks=1,output_sha256=snap.digest(data)))
            j.emit('cuCtxDestroy_v2','entered');j.emit('cuCtxDestroy_v2','returned',return_code=0)
        return None,dict(backend='cuda',gpu_execution_verified=True,input_sha256=snap.digest(packed),output_sha256=snap.digest(data),transport=dict(command_status='completed',cases=1,input_bytes=len(packed),output_bytes=4))
    def child(self):
        import portable_backend
        def copy(capture,suite):
            (capture/'generated.cu').write_bytes(self.f.f.cuda);(capture/'compiled.cubin').write_bytes(self.f.f.image)
        cli=SimpleNamespace(**{**vars(self.cli),'copy_generated':copy})
        with patch.dict(os.environ,dict(NIKKE_SLANG_GENERATION_REQUIRED='1',NIKKE_CUDA_ARTIFACT='cubin',NIKKE_SLANG_ROOT=str(self.f.f.base),NIKKE_SLANG_GENERATION_CACHE=str(self.f.f.base))),patch.object(execution,'live_job',return_value=dict(job_memory_limit_bytes=2147483648,job_limit_flags=0x2200)),patch.object(portable_backend,'execute',side_effect=self.cpu_execute):
            execution.child(cli,self.capture,self.claim_sha)
    def test_mirrored_ownership_and_child_complete_without_calculation_promotion(self):
        claim,a=self.ownership();self.assertEqual(claim['consumer_package_id'],self.manifest['package_id'])
        self.child();result=self.cli.load(self.capture/'dispatch.json')
        self.assertTrue(result['gpu_execution_completed']);self.assertFalse(result['calculation_verified']);self.assertTrue(result['independent_post_audit_required'])
        self.assertEqual(self.gpu_calls,1);self.assertTrue((self.capture/'prepared-child-started.json').exists())
        before=(self.capture/'phases.jsonl').read_bytes()
        with self.assertRaises(FileExistsError):self.child()
        self.assertEqual((self.capture/'phases.jsonl').read_bytes(),before)
        self.assertEqual(self.gpu_calls,1)
    def test_foreign_claim_sha_and_consumer_rejected(self):
        with self.assertRaisesRegex(ValueError,'claim SHA'):execution.ownership(self.cli,self.manifest,self.capture,'0'*64)
        with self.assertRaisesRegex(ValueError,'identity/protocol'):execution.ownership(self.cli,dict(self.manifest,package_id='0'*64),self.capture,self.claim_sha)
    def test_partial_claim_mirror_never_executes(self):
        (self.f.f.tx/'gpu-execution-claimed.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'mirrors'):self.child()
        self.assertEqual(self.gpu_calls,0);self.assertFalse((self.capture/'prepared-child-started.json').exists())
    def test_modified_authority_and_evidence_anchors_rejected(self):
        (self.f.stage/'command.json').write_text('{}')
        with self.assertRaises(ValueError):self.child()
        self.assertEqual(self.gpu_calls,0)
    def test_mismatched_run_nonce_rejected_before_child_marker(self):
        run=json.loads(json.dumps(self.run));run['binding']['transaction_nonce']='0'*32;self.save('run.json',run)
        with self.assertRaisesRegex(ValueError,'run/ownership'):self.child()
        self.assertEqual(self.gpu_calls,0);self.assertFalse((self.capture/'prepared-child-started.json').exists())
    def test_success_flag_without_actual_ordered_driver_boundaries_is_not_complete(self):
        self.emit_trace=False
        with self.assertRaisesRegex(ValueError,'native trace incomplete'):self.child()
        self.assertFalse((self.capture/'dispatch.json').exists());self.assertTrue((self.capture/'prepared-child-started.json').exists())
        failure=self.cli.load(self.capture/'prepared-child-failure.json');self.assertTrue(failure['shared_execute_entered']);self.assertIsNone(failure['gpu_calls'])
        with self.assertRaises(FileExistsError):self.child()
        self.assertEqual(self.gpu_calls,1)
    def test_real_platform_gate_precedes_any_gpu_call(self):
        with patch.object(execution,'is_windows',return_value=False),self.assertRaisesRegex(ValueError,'requires Windows'):self.child()
        self.assertEqual(self.gpu_calls,0)
    def test_unrequested_resource_observer_is_rejected_before_gpu_marker(self):
        with patch.dict(os.environ,NIKKE_CUDA_RESOURCE_OBSERVATION='1'),self.assertRaisesRegex(ValueError,'observation setting mismatch'):self.child()
        self.assertEqual(self.gpu_calls,0);self.assertFalse((self.capture/'prepared-child-started.json').exists())


if __name__=='__main__':unittest.main()
