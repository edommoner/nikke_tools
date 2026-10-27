"""A timeout stays failed while unchanged completed receipts cover one attempt."""
import copy,json,os,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','tests','research')]
import test_portable_staged_preflight as fixture
import portable_staged_continuation as cont
import portable_continuation_package as capsule
flow=fixture.flow;cli=fixture.cli;packet=fixture.packet


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.StagedPreflightTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        f=self.f;f.c.module=lambda _:packet
        f.begin()
        with patch.object(flow,'os',SimpleNamespace(name='posix',fsync=os.fsync,getpid=lambda:1000)):
            flow.group(f.c,f.tx,0,f.root/'group0')
        self.old=cli.load(f.tx/'transaction.json');self.failed=f.root/'failed';proof=self.failed/'proof';proof.mkdir(parents=True)
        cli.write(f.tx/'group-claim-1.json',dict(capture=str(proof),nonce=self.old['nonce'],group_index=1))
        self.recipe=packet.recipe('owned','preflight-native-group','metal',self.failed,f.root/'original',3,dict(transaction=str(f.tx),group_index='1'))
        cli.write(self.failed/'recipe.json',self.recipe)
        self.facts=dict(passed=False,timed_out=True,timeout_seconds=3,final_child_exit_code=-15,cleanup_error=None,observation_error=None)
        cli.write(self.failed/'execution.json',self.facts)
        (proof/'phases.jsonl').write_text('{}\n')
        self.current=copy.deepcopy(f.m);self.current['package_id']='new-owned'
        self.pkg=f.root/'capsule';self.pkg.mkdir();cli.write(self.pkg/'gpu-package.json',self.current)
        self.c=SimpleNamespace(**{**vars(f.c),'ROOT':self.pkg,'verify_package':lambda _:self.current})
        self.info=dict(manifest=f.m,config=f.c.SUITES['fixture'],smoke=[])
        p=patch.object(cont,'owner_snapshot',return_value=self.info);p.start();self.addCleanup(p.stop)
        p=patch.object(cont,'validate_lineage',side_effect=lambda c,m,o,r:None if m['golden']==o['golden'] else (_ for _ in ()).throw(ValueError('golden')));p.start();self.addCleanup(p.stop)
        p=patch.object(cont,'os',SimpleNamespace(name='posix'));p.start();self.addCleanup(p.stop)
        self.tx=f.root/'resume'
    def resume(self):return cont.resume(self.c,self.tx,self.f.tx,1,'metal')
    def tail(self):
        with patch.object(flow,'os',SimpleNamespace(name='posix',fsync=os.fsync,getpid=lambda:2000)):
            return flow.group(self.c,self.tx,0,self.f.root/'tail')
    def test_retains_prefix_and_tests_and_computes_only_unfinished_case(self):
        before=list(self.f.calls);r=self.resume()
        self.assertEqual(self.f.calls,before);self.assertEqual(r['original_completed_inputs'],2)
        self.assertEqual(r['original_native_cases'],1);self.assertFalse(r['original_failed_stage_verified']);self.assertFalse(r['native_values_reused'])
        self.assertFalse((self.tx/'cpu-tests.json').exists());self.assertEqual(cli.load(self.tx/'transaction.json')['case_groups'],[[2]])
        self.assertNotIn('must-never-be-written',(self.tx/'original-evidence.json').read_text())
        self.tail();self.assertEqual(self.f.calls,self.f.domains)
        r=flow.admit(self.c,self.current,self.tx,'metal',self.f.gpu)
        self.assertTrue(r['all_native_preflight_verified']);self.assertEqual((r['input_count'],r['native_cases']),(3,2))
        self.assertIsNotNone(r['continuation_parent']);self.assertFalse(r['original_timeout']['envelope']['original_stage_verified'])
        self.assertFalse((self.failed/'proof/result.json').exists());self.assertFalse((self.failed/'proof/artifacts.json').exists())
    def test_original_failure_or_completed_receipts_cannot_change_after_resume(self):
        self.resume();self.tail()
        p=self.failed/'execution.json';r=cli.load(p);r['new_field']='mutated';cli.write(p,r)
        with self.assertRaisesRegex(ValueError,'evidence bytes changed'):flow.admit(self.c,self.current,self.tx,'metal',self.f.gpu)
    def test_gpu_input_uses_new_owner_without_promoting_original_timeout(self):
        self.resume();self.tail();self.f.gpu.mkdir()
        cli.write(self.f.gpu/'run.json',dict(package_id='new-owned',backend='metal',mode='staged-gpu',input_protocol=flow.PROTOCOL))
        r=flow.prepare_gpu_input(self.c,self.current,self.tx,self.f.gpu,'metal')
        self.assertTrue(r['all_native_preflight_verified']);self.assertFalse(r['calculation_verified'])
        flow.claim_execution(self.c,self.tx,self.f.gpu)
        self.assertEqual(flow.read_gpu_input(self.c,self.current,self.f.gpu),(self.f.data,1))
        self.assertFalse((self.f.tx/'gpu-execution-claimed.json').exists())
        run=cli.load(self.f.gpu/'run.json');run['package_id']='owned';cli.write(self.f.gpu/'run.json',run)
        with self.assertRaisesRegex(ValueError,'before GPU'):flow.admit(self.c,self.current,self.tx,'metal',self.f.gpu)
    def test_unfinished_tail_and_wrong_parent_cannot_become_complete(self):
        self.resume()
        with self.assertRaises(FileNotFoundError):flow.admit(self.c,self.current,self.tx,'metal',self.f.gpu)
        c=cli.load(self.tx/'transaction.json');c['resume_parent']['completed_inputs']=1;cli.write(self.tx/'transaction.json',c)
        with self.assertRaises(ValueError):flow.context(self.c,self.tx)
    def test_original_gpu_execution_and_replay_are_rejected(self):
        self.f.gpu.mkdir()
        with self.assertRaisesRegex(ValueError,'before GPU'):self.resume()
        self.f.gpu.rmdir();self.resume()
        with self.assertRaises(FileExistsError):cont.resume(self.c,self.f.root/'replay',self.f.tx,1,'metal')
    def test_cleanup_fault_non_timeout_success_or_no_smaller_groups_are_rejected(self):
        for change in (dict(timed_out=False),dict(passed=True),dict(cleanup_error='failed'),dict(observation_error='unknown'),dict(timeout_seconds=181)):
            cli.write(self.failed/'execution.json',dict(self.facts,**change))
            with self.subTest(change=change),self.assertRaises(ValueError):self.resume()
        cli.write(self.failed/'execution.json',self.facts)
        for size in (0,2,True):
            with self.subTest(size=size),self.assertRaises(ValueError):cont.resume(self.c,self.tx,self.f.tx,size,'metal')
    def test_failed_windows_job_requires_containment_priority_and_preservation_observation(self):
        facts=dict(self.facts,below_normal_priority=True);cli.write(self.failed/'execution.json',facts)
        (self.failed/'proof/phases.jsonl').write_text(json.dumps(dict(pid=101))+'\n')
        from windows_validation_observer import compare_snapshots
        observation=dict(before={},after={})
        self.c.job_contained=lambda *a,**k:(True,101)
        with patch.object(cont,'os',SimpleNamespace(name='nt')),patch('windows_validation_observer.compare_snapshots',return_value={'missing_existing_processes':[]}):
            observation['comparison']={'missing_existing_processes':[]};cli.write(self.failed/'observation.json',observation)
            r=cont._failed_timeout(self.c,self.f.m,self.old,1);self.assertTrue(r['envelope']['containment_verified']);self.assertFalse(r['envelope']['original_stage_verified'])
            self.c.job_contained=lambda *a,**k:(False,None)
            with self.assertRaises(ValueError):cont._failed_timeout(self.c,self.f.m,self.old,1)
    def test_wrapper_request_is_explicit_and_does_not_add_gpu_or_compile_flags(self):
        request=dict(parent_transaction=str(self.f.tx),group_size='1')
        with patch.object(packet,'is_windows',return_value=True):
            plan=packet.recipe('new-owned','preflight-resume','cuda',self.f.root/'stage',self.f.root/'original',180,request)
        self.assertEqual(packet.proof_arguments(plan),['preflight-resume','--capture',str(self.f.root/'stage/proof'),'--backend','cuda','--parent-transaction',str(self.f.tx),'--group-size','1'])
        r=self.resume();self.assertTrue(packet.verified_staged(r,'preflight-resume','new-owned'))
        for change in (dict(native_values_reused=True),dict(original_failed_stage_verified=True),dict(calculation_verified=True)):
            self.assertFalse(packet.verified_staged(dict(r,**change),'preflight-resume','new-owned'))


class CapsuleSourceTests(unittest.TestCase):
    def source(self):
        names=('host','outside','static_input','exclusive','terminal_cpu_stage','prepare_gpu_input','claim_execution','read_gpu_input','finish_gpu')
        flow_source='\n'.join('def '+n+'():return 1' for n in names)+"\ndef group(c,index):\n for i in c['case_groups'][index]:\n  native_value(i)\n"
        return {'scripts/nikke_gpu.py':'def native_value(x):return x\ndef main():pass\n','app/portable_staged_preflight.py':flow_source}
    def test_only_control_entry_changes_leave_numeric_and_transport_functions_exact(self):
        a=self.source();b=dict(a);b['scripts/nikke_gpu.py']=b['scripts/nikke_gpu.py'].replace('def main():pass','def main():print(1)');capsule.source_guard(a,b)
        for name,old,new in [('scripts/nikke_gpu.py','return x','return 0'),('app/portable_staged_preflight.py','native_value(i)','native_value(0)'),('app/portable_staged_preflight.py','def static_input():return 1','def static_input():return 0')]:
            b=dict(a);b[name]=b[name].replace(old,new)
            with self.subTest(name=name),self.assertRaises(ValueError):capsule.source_guard(a,b)
    def test_unrelated_payload_or_golden_change_is_not_a_controller_capsule(self):
        class C:pass
        c=C();c.ROOT=ROOT;c.sha=cli.sha
        with fixture.tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'gpu-package.json').write_text('{}')
            original=dict(package_id='old',purpose='sealed',suite='x',golden={'same':1},files=[dict(path='gpu/x.slang',bytes=1,sha256='1')])
            current=copy.deepcopy(original);current['controller_continuation']=dict(schema=capsule.SCHEMA,base_package_id='old',base_manifest_sha256=cli.sha(b'{}'))
            current['files']+= [dict(path=n,bytes=0,sha256='0') for n in capsule.ADDED]
            current['files'][0]['sha256']='changed'
            with self.assertRaisesRegex(ValueError,'native/GPU/data/test'):capsule.validate_lineage(c,current,original,root)
            current['golden']={'different':1}
            with self.assertRaisesRegex(ValueError,'owner/golden'):capsule.validate_lineage(c,current,original,root)


if __name__=='__main__':unittest.main()
