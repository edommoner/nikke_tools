"""One new owner consumes one retained failure; failed execution is not retried."""
import json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_partitioned_cuda_owner as owner
import portable_partitioned_cuda_receipt as receipt
from test_portable_partitioned_cuda_receipt import c


class OwnerTests(unittest.TestCase):
    def fixture(self,root):
        package=root/'package';(package/'research').mkdir(parents=True)
        golden=dict(entries=[dict(name='one')],output_sha256='a'*64)
        reference=dict(calculation_verified=True,comparison=dict(entries=golden['entries'],logical_output_sha256=golden['output_sha256'],raw_output_sha256='b'*64))
        path=package/'research/partitioned-cuda-native-reference.json';c.write(path,reference)
        m=dict(package_id='fixed',purpose='sealed',golden=golden,partitioned_cuda_execution=dict(schema=owner.MODE,batch_size=16,maximum_gpu_seconds=60,native_reference_sha256=c.sha(path.read_bytes())))
        cli=SimpleNamespace(ROOT=package,verify_package=lambda p:m,load=c.load,sha=c.sha,write=c.write,check_records=c.check_records,
            job_contained=lambda *a,**k:(False,None),environment_preserved=lambda *a:False,collect=lambda *a:None)
        return cli,m

    def test_metadata_and_complete_reference_must_match_before_any_stage(self):
        for kind in ('limit','batch','reference'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                cli,m=self.fixture(Path(tmp))
                if kind=='limit':m['partitioned_cuda_execution']['maximum_gpu_seconds']=61
                elif kind=='batch':m['partitioned_cuda_execution']['batch_size']=1
                else:(cli.ROOT/'research/partitioned-cuda-native-reference.json').write_text('{}')
                with self.assertRaises(ValueError):owner.manifest(cli)

    def test_stage_budgets_are_rejected_before_source_or_claim_access(self):
        for stage,value in (('gpu',61),('prepare',181),('smoke',61),('gpu',True),('gpu',0)):
            with self.subTest(stage=stage,value=value),self.assertRaises(ValueError):owner.run(None,stage,None,None,timeout=value)

    def test_retained_failure_has_a_stable_ledger_across_package_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cli,m=self.fixture(root)
            state=dict(old_capture=str(root/'old/gpu'),old_failure_sha256='a'*64,claims=[dict(path='old-claim',sha256='b'*64)])
            first=owner.ledger(cli,state);cli.ROOT=root/'another-package'
            self.assertEqual(first,owner.ledger(cli,state));self.assertIn('.partitioned-cuda-claims',first.parts)

    def test_failed_attempt_preserves_new_claim_and_cannot_be_dispatched_twice(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ):
            root=Path(tmp);cli,m=self.fixture(root);prepared=root/'prepared';prepared.mkdir();capture=root/'gpu'
            state=dict(old_capture=str(root/'old/gpu'),old_failure_sha256='a'*64,claims=[],auditor_root=str(root/'auditor'),source_capture=str(root/'audit'))
            context=dict(nonce='fresh',settings=dict(slang_root=str(root/'sdk'),generation_cache=str(root/'cache')))
            cli.run_job=Mock(return_value=dict(passed=False));(cli.ROOT/'gpu-package.json').write_text('{}')
            with patch.object(owner,'os',SimpleNamespace(name='nt',environ=os.environ)),patch.object(owner,'prepared',return_value=(context,state)),patch.object(receipt,'check',return_value=True):
                result=owner.run(cli,'gpu',capture,root/'workspace',prepare_capture=prepared,timeout=60)
                self.assertFalse(result['passed']);self.assertFalse(result['gpu_execution_verified'])
                self.assertTrue((cli.ROOT/owner.CLAIM).is_file());self.assertTrue(owner.ledger(cli,state).is_file())
                with self.assertRaises(FileExistsError):owner.run(cli,'gpu',capture,root/'workspace',prepare_capture=prepared,timeout=60)
                cli.run_job.assert_called_once()


if __name__=='__main__':unittest.main()
