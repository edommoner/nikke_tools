"""Saved failure diagnosis cannot grant retries or native/cache proof."""
import copy,importlib.util,json,shutil,struct,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_staged_failure as audit
from windows_validation_observer import compare_snapshots
spec=importlib.util.spec_from_file_location('failure_test_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
spec=importlib.util.spec_from_file_location('failure_test_packet',ROOT/'scripts/run-gpu-packet.py');packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)


class StagedFailureTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.base=Path(tmp.name).resolve()
        self.root=self.base/'packet';self.outer=self.base/'failed';self.proof=self.outer/'proof';self.tx=self.base/'transaction'
        for p in (self.root,self.proof,self.tx):p.mkdir(parents=True)
        for name in ('app/portable_backend.py','app/portable_slang_generation.py','app/portable_generation_cache.py','scripts/nikke_gpu.py','research/portable_phase_audit.py','scripts/run-gpu-packet.py'):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
        self.write=cli.write;self.data=struct.pack('<II',1,42)
        self.m=dict(schema=1,suite='fixture',purpose='sealed',golden=dict(input_sha256=cli.sha(self.data),entries=[dict(input_sha256=cli.sha(self.data[4:]),name='case')]))
        self.m['package_id']=cli.package_id(self.m);self.write(self.root/'gpu-package.json',self.m)
        self.receipt=cli.transport_input_receipt(self.m,self.data,1)
        self.write(self.proof/'run.json',dict(package_id=self.m['package_id'],backend='cuda',mode='staged-gpu',input_protocol='staged-prepared-v1',gpu_retry_count=0))
        self.write(self.proof/'runtime.json',dict(slang_root=None,generation_cache_enabled=True,generation_cache_required=True))
        facts=dict(passed=False,timed_out=False,timeout_seconds=60,child_exit_code=1,final_child_exit_code=1,below_normal_priority=True,error=None,cleanup_error=None,observation_error=None)
        self.write(self.proof/'execution.json',facts);self.write(self.outer/'execution.json',dict(facts,timed_out=True,timeout_seconds=180,child_exit_code=None))
        projection=json.loads((ROOT/'tests/fixtures/staged-missing-slang-phase-projection-v1.json').read_text())['rows']
        self.rows=[dict(r,monotonic_ns=i+1,wall_time_ns=i+1) for i,r in enumerate(projection)]
        (self.proof/'phases.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.rows))
        (self.proof/'stderr.log').write_text('ValueError: Slang cache compiler identity absent\n')
        (self.proof/'input.bin').write_bytes(self.data);self.write(self.proof/'input-preflight.json',self.receipt)
        request=dict(transaction=str(self.tx),linked_package=str(self.base/'compiler'),linked_capture=str(self.base/'link'))
        self.write(self.outer/'recipe.json',packet.recipe(self.m['package_id'],'staged-gpu-linked','cuda',self.outer,self.base/'original',180,request))
        self.write(self.tx/'transaction.json',dict(package_id=self.m['package_id'],gpu_capture=str(self.proof),package_root=str(self.root),nonce='owned'))
        self.write(self.tx/'gpu-execution-claimed.json',dict(package_id=self.m['package_id'],capture=str(self.proof),nonce='owned'))
        self.write(self.root/'gpu-claimed-cuda.json',dict(package_id=self.m['package_id'],capture=str(self.proof),transaction=str(self.tx),transaction_nonce='owned'))
        self.write(self.root/'packet-stage-claimed-staged-gpu-linked-cuda.json',dict(package_id=self.m['package_id'],capture=str(self.outer)))
        self.write(self.proof/'staged-preflight.json',dict(transaction=str(self.tx),transaction_nonce='owned',transaction_sha256=cli.sha((self.tx/'transaction.json').read_bytes()),input=self.receipt))
        def job(directory,pid,ppid):
            state=dict(child_pid=pid,child_ppid=ppid,child_creation_filetime_ticks=1,job_members=[pid],job_memory_limit_bytes=2147483648,observed_unix_ns=0)
            self.write(directory/'job.json',dict(records=[dict(child_pid=pid,wrapper_pid=ppid,pre_gate_verified=True,inspection_error=None,pre_gate=state,post_wait=dict(state,job_members=[],observed_unix_ns=100))]))
        job(self.proof,67876,20);job(self.outer,20,10)
        (self.outer/'preparation.jsonl').write_text(json.dumps(dict(pid=20,monotonic_ns=1,wall_time_ns=1))+'\n')
        snapshot=dict(processes=[],service_status='unverified');observation=dict(before=snapshot,after=snapshot,comparison=compare_snapshots(snapshot,snapshot))
        self.write(self.outer/'observation.json',observation);self.write(self.proof/'observation.json',observation)

    def check(self,name='audit.json',expected=None):
        with patch('portable_continuation_package.owner_snapshot',return_value=dict(manifest=self.m)) as owner,cli.forbid_gpu(),patch.object(cli,'native_value',side_effect=AssertionError('No native calculation')):
            result=audit.check(cli,self.root,self.outer,self.base/name,expected or self.m['package_id'])
        owner.assert_called_once();return result

    def test_original_projection_matches_only_the_narrow_failure_pattern(self):
        self.assertEqual(audit.validate_trace(self.rows),67876)
        for kind in ('missing','api','order','pid','exception'):
            rows=copy.deepcopy(self.rows)
            if kind=='missing':rows.pop()
            elif kind=='api':rows.append(dict(stage='cuInit',state='entered',pid=67876))
            elif kind=='order':rows[1],rows[2]=rows[2],rows[1]
            elif kind=='pid':rows[-1]['pid']=True
            else:rows[-1]['exception']='TimeoutError'
            with self.subTest(kind=kind),self.assertRaises(ValueError):audit.validate_trace(rows)

    def test_complete_saved_fixture_preserves_claims_and_refuses_execution(self):
        before=cli.file_records(self.root,['gpu-claimed-cuda.json','packet-stage-claimed-staged-gpu-linked-cuda.json'])
        result=self.check()
        self.assertTrue(result['passed']);self.assertTrue(result['prepared_input_verified'])
        for key in ('execution_permitted','native_admission_revalidated','linked_artifact_revalidated','host_revalidated','calculation_verified','environment_preservation_verified','claims_modified'):self.assertFalse(result[key])
        self.assertEqual(result['gpu_calls'],0);cli.check_records(self.root,before)
        with self.assertRaises(FileExistsError):self.check()

    def test_dispatch_result_partial_input_and_unknown_terminal_fail_closed(self):
        for kind in ('readback','partial','input','terminal','trace','job','source'):
            with self.subTest(kind=kind):
                if kind in ('readback','partial'):
                    target=self.proof/('readback.bin' if kind=='readback' else 'readback.bin.partial');old=None;target.write_bytes(b'partial')
                else:
                    target=self.proof/({'input':'input.bin','terminal':'execution.json','trace':'phases.jsonl','job':'job.json'}.get(kind,'../../packet/app/portable_backend.py'));target=target.resolve();old=target.read_bytes()
                    if kind=='input':target.write_bytes(b'changed')
                    elif kind=='terminal':d=cli.load(target);d['final_child_exit_code']=True;self.write(target,d)
                    elif kind=='trace':target.write_bytes(old.rstrip(b'\n'))
                    elif kind=='job':d=cli.load(target);d['records'][0]['post_wait']['job_members']=[67876];self.write(target,d)
                    else:target.write_text(target.read_text().replace('def execute(', 'def changed_execute(',1))
                with self.assertRaises((ValueError,KeyError)):self.check(kind+'.json')
                self.assertFalse(cli.load(self.base/(kind+'.json'))['passed'])
                if old is None:target.unlink()
                else:target.write_bytes(old)

    def test_failure_stage_cannot_promote_a_forged_gpu_success(self):
        result=self.check();request=dict(expected_package_id=self.m['package_id'])
        self.assertTrue(packet.verified_failure(result,request))
        for key,value in [('calculation_verified',True),('execution_permitted',True),('gpu_calls',False),('native_admission_revalidated',True),('package_id','another')]:
            with self.subTest(key=key):self.assertFalse(packet.verified_failure(dict(result,**{key:value}),request))

    def test_outputs_cannot_modify_any_original_evidence_tree(self):
        for path in (self.root/'new.json',self.proof/'new.json',self.tx/'new.json'):
            with self.subTest(path=path),self.assertRaises(ValueError):audit.check(cli,self.root,self.outer,path,self.m['package_id'])
            self.assertFalse(path.exists())

    def test_unknown_owner_rejected_before_loading_its_verifier(self):
        with patch('portable_continuation_package.owner_snapshot',side_effect=AssertionError('Unpinned owner must not execute')) as owner,self.assertRaises(ValueError):
            audit.check(cli,self.root,self.outer,self.base/'bad-owner.json','b'*64)
        owner.assert_not_called();self.assertFalse(cli.load(self.base/'bad-owner.json')['passed'])

    def test_actual_windows_diagnostic_keeps_failure_and_execution_scopes_separate(self):
        result=json.loads((ROOT/'tests/fixtures/staged-failure-windows-audit-v1.json').read_text(encoding='utf-8'))
        stage_result=json.loads((ROOT/'tests/fixtures/staged-failure-windows-stage-v1.json').read_text(encoding='utf-8'))
        self.assertEqual(stage_result['proof_result'],result)
        self.assertTrue(stage_result['stage_verified']);self.assertFalse(stage_result['calculation_verified'])
        self.assertEqual(result['input_count'],106);self.assertTrue(result['execution_claim_consumed'])
        self.assertTrue(packet.verified_failure(result,dict(expected_package_id=result['package_id'])))
        for key in ('execution_permitted','native_admission_revalidated','linked_artifact_revalidated','host_revalidated','calculation_verified','environment_preservation_verified'):
            self.assertFalse(result[key])


if __name__=='__main__':unittest.main()
