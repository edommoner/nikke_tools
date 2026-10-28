"""Re-read exactly the failed launch; never admit or retry a new GPU call."""
import contextlib,copy,ctypes,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_partitioned_cuda_origin as origin
import portable_backend as backend
import portable_staged_preflight as staged
import portable_linked_artifact as linked


def trace():
    stages=['cuInit','cuDeviceGet','cuDeviceComputeCapability','cuDeviceGetName','cuCtxCreate_v2','cuModuleLoadData',
            'cuModuleGetFunction','cuModuleGetGlobal_v2',*(['cuMemAlloc_v2']*3),'cuMemcpyHtoD_v2','cuMemsetD8_v2','cuMemcpyHtoD_v2','cuLaunchKernel','cuCtxDestroy_v2']
    rows=[]
    for s in stages:
        rows.extend([dict(stage=s,state='entered'),dict(stage=s,state='returned',return_code=2 if s=='cuLaunchKernel' else 0)])
    return rows


class OriginTests(unittest.TestCase):
    def fixture(self,root):
        package=root/'package';outer=root/'outer';proof=outer/'proof';tx=root/'tx'
        for p in (package,proof,tx):p.mkdir(parents=True)
        save=lambda p,r:p.write_text(json.dumps(r))
        ledger=root/'ledger';ledger.write_bytes(b'claimed')
        for p in (package/'gpu-claimed-cuda.json',package/'packet-stage-claimed-staged-gpu-linked-cuda.json',tx/'gpu-execution-claimed.json'):p.write_bytes(b'claimed')
        saved=dict(transaction=str(tx),all_native_preflight_verified=True,input_count=106,native_cases=63)
        save(proof/'staged-preflight.json',saved);save(tx/'transaction.json',dict(recovery_parent=dict(ledger=str(ledger))))
        save(proof/'linked-artifact-request.json',dict(package='producer',capture='linked'))
        identity=dict(schema=1,provider=linked.PROVIDER,artifact='cubin')
        receipt=dict(identity=identity,key=linked.key(identity),artifact_bytes=1,artifact_sha256='a'*64,enabled=True,reused=True)
        rows=trace()+[dict(stage=linked.STAGE,state='verified',receipt=receipt)]
        (proof/'phases.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        for p in (outer,proof):
            save(p/'execution.json',dict(passed=False,timed_out=False,child_exit_code=1,final_child_exit_code=1,below_normal_priority=True))
            save(p/'job.json',dict(records=[dict(child_pid=77,post_wait=dict(job_members=[]))]))
            save(p/'observation.json',dict(before={},after={},comparison=dict(missing_existing_processes=[])))
        (outer/'preparation.jsonl').write_text(json.dumps(dict(pid=77))+'\n')
        m=dict(package_id=origin.OWNER,golden=dict(frozen=True))
        cli=SimpleNamespace(verify_package=lambda p:m,load=lambda p:json.loads(p.read_text()),sha=lambda b:hashlib.sha256(b).hexdigest(),
                            forbid_gpu=contextlib.nullcontext,job_contained=lambda *a,**k:(True,77),saved_linked_admission=Mock(return_value=dict(receipt=receipt,artifact='exact.cubin')))
        return cli,package,outer,proof,saved

    def test_original_exact_failure_and_admission_are_reused_without_new_permission(self):
        with tempfile.TemporaryDirectory() as tmp:
            cli,package,outer,proof,saved=self.fixture(Path(tmp))
            with patch.object(staged,'admit',return_value=saved) as admit,patch('windows_validation_observer.compare_snapshots',return_value=dict(missing_existing_processes=[])):
                r=origin.inspect_original(cli,package,outer)
            self.assertTrue(r['native_admission_revalidated']);self.assertEqual(r['input_count'],106);self.assertEqual(len(r['native_events']),32)
            self.assertFalse(r['execution_permitted']);self.assertFalse(r['original_stage_passed']);self.assertFalse(r['claims_modified'])
            admit.assert_called_once_with(cli,cli.verify_package(package),Path(saved['transaction']),'cuda',proof.resolve())

    def test_wrong_or_successful_launch_incomplete_copy_or_cleanup_and_compiler_rejected(self):
        for kind in ('success','different-error','missing','extra','cleanup','compile'):
            rows=trace()
            if kind=='success':rows[-3]['return_code']=0
            elif kind=='different-error':rows[-3]['return_code']=701
            elif kind=='missing':del rows[-4]
            elif kind=='extra':rows.insert(-2,dict(stage='cuMemcpyDtoH_v2',state='entered'))
            elif kind=='cleanup':rows[-1]['return_code']=1
            else:rows.append(dict(stage='nvrtcCompileProgram',state='entered'))
            with self.subTest(kind=kind),self.assertRaises(ValueError):origin.failure_trace(rows)

    def test_changed_claim_or_admission_is_not_accepted(self):
        for kind in ('admission','claim'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                cli,package,outer,proof,saved=self.fixture(Path(tmp))
                def admit(*args):
                    if kind=='claim':(package/'gpu-claimed-cuda.json').write_bytes(b'changed')
                    return dict(saved,input_count=1) if kind=='admission' else saved
                with patch.object(staged,'admit',side_effect=admit),patch('windows_validation_observer.compare_snapshots',return_value=dict(missing_existing_processes=[])),self.assertRaises(ValueError):
                    origin.inspect_original(cli,package,outer)

    def test_gpu_compiler_and_library_bypass_are_blocked_and_restored(self):
        original=backend.execute_cuda_batches;cli=SimpleNamespace(forbid_gpu=contextlib.nullcontext)
        with origin.gpu_forbidden(cli):
            for function in (backend.execute_cuda_batches,backend.compile_cuda_source,backend._cuda_module):
                with self.assertRaisesRegex(RuntimeError,'forbidden'):function()
            for name in ('nvcuda.dll','nvrtc.dll','nvJitLink.dll','libslang.dylib'):
                with self.subTest(name=name),self.assertRaisesRegex(RuntimeError,'forbidden'):ctypes.CDLL(name)
        self.assertIs(backend.execute_cuda_batches,original)

    def test_unbounded_or_non_windows_entry_is_rejected_before_job(self):
        with patch.object(origin,'os',SimpleNamespace(name='nt')):
            for t in (0,181,True):
                with self.assertRaisesRegex(ValueError,'1..180'):origin.run(None,None,None,None,None,None,None,t)
        with patch.object(origin,'os',SimpleNamespace(name='posix')),self.assertRaisesRegex(ValueError,'Windows'):
            origin.run(None,None,None,None,None,None,None)


if __name__=='__main__':unittest.main()
