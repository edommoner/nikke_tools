"""Every original test group remains mandatory before native or GPU admission."""
import copy,os,sys,unittest,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','tests','research')]
import test_portable_staged_preflight as fixture
import portable_staged_tests as staged
import portable_cpu_tests as worker
flow=fixture.flow;cli=fixture.cli;packet=fixture.packet


class StagedTestGroupsTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.StagedPreflightTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.names=['test_owned_'+uuid.uuid4().hex+'_'+str(i)+'.py' for i in range(3)]
        self.testroot=self.f.pkg/'tests';self.testroot.mkdir()
        for name in self.names:
            (self.testroot/name).write_text('import unittest\nclass TestOwned(unittest.TestCase):\n def test_owned(self):self.assertEqual(2+2,4)\n')
            self.addCleanup(lambda n=name:sys.modules.pop(n[:-3],None))
        self.f.c.SUITES['fixture']['tests']=self.names
        self.f.m['files']=cli.file_records(self.f.pkg,['tests/'+n for n in self.names]);cli.write(self.f.pkg/'gpu-package.json',self.f.m)
    def begin(self):return flow.begin(self.f.c,self.f.tx,'metal',self.f.gpu,2,test_group_size=2)
    def run_group(self,index):
        proxy=SimpleNamespace(getpid=lambda:8000+index)
        with patch.object(staged,'os',proxy),patch.object(worker,'os',proxy):
            return staged.run_group(self.f.c,self.f.tx,index,self.f.root/('tests'+str(index)))
    def ready_tests(self):self.begin();self.run_group(0);self.run_group(1)
    def test_plan_performs_no_unit_or_native_calculation_and_blocks_native(self):
        r=self.begin();self.assertEqual(r['mode'],'staged-preflight-plan-only');self.assertFalse(r['cpu_tests_verified'])
        self.assertFalse((self.f.tx/'cpu-tests.json').exists());self.assertEqual(self.f.calls,[])
        with self.assertRaises(FileNotFoundError):flow.group(self.f.c,self.f.tx,0,self.f.root/'premature-native')
        self.assertEqual(self.f.calls,[]);self.assertFalse((self.f.tx/'gpu-execution-claimed.json').exists())
    def test_all_original_tests_in_order_then_every_native_case_are_still_required(self):
        self.ready_tests();c=cli.load(self.f.tx/'transaction.json');stages=staged.admit_tests(self.f.c,self.f.m,c)
        self.assertEqual(len(stages),2);self.assertEqual(self.f.calls,[])
        for i,want in enumerate((self.names[:2],self.names[2:])):
            r=cli.load(self.f.root/('tests'+str(i))/'result.json');self.assertEqual(r['patterns'],want)
            self.assertEqual(r['tests'],len(want));self.assertFalse(r['all_cpu_tests_verified']);self.assertFalse(r['calculation_verified'])
        self.f.groups();r=flow.admit(self.f.c,self.f.m,self.f.tx,'metal',self.f.gpu)
        self.assertEqual(self.f.calls,self.f.domains);self.assertTrue(r['all_native_preflight_verified'])
        self.assertEqual(len(r['stage_envelopes']),5);self.assertFalse((self.f.tx/'cpu-tests.json').exists())
    def test_missing_group_replay_and_registry_drift_are_rejected(self):
        self.begin();self.run_group(0)
        with self.assertRaises(FileNotFoundError):staged.admit_tests(self.f.c,self.f.m,cli.load(self.f.tx/'transaction.json'))
        with self.assertRaises(FileExistsError):staged.run_group(self.f.c,self.f.tx,0,self.f.root/'replay-tests')
        self.f.c.SUITES['fixture']['tests']=self.names[::-1]
        with self.assertRaisesRegex(ValueError,'registry/partition'):flow.context(self.f.c,self.f.tx)
    def test_wrong_pid_case_order_or_partial_receipt_cannot_admit(self):
        self.ready_tests();p=self.f.root/'tests1';original=cli.load(p/'result.json')
        mutations=[dict(child_pid=8000),dict(group_index=False),dict(patterns=self.names[:1]),dict(tests=True),dict(all_cpu_tests_verified=True),dict(gpu_calls=False),dict(transaction_nonce='other')]
        for change in mutations:
            cli.write(p/'result.json',dict(original,**change));cli.collect(p,p/'artifacts.json')
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'identity/coverage'):
                staged.admit_tests(self.f.c,self.f.m,cli.load(self.f.tx/'transaction.json'))
        cli.write(p/'result.json',original);cli.collect(p,p/'artifacts.json')
        rows=cli.load(p/'cpu-tests.json');rows[0]['runner_pid']=123;cli.write(p/'cpu-tests.json',rows);cli.collect(p,p/'artifacts.json')
        with self.assertRaises(ValueError):staged.admit_tests(self.f.c,self.f.m,cli.load(self.f.tx/'transaction.json'))
    def test_missing_test_log_is_rejected_even_if_inventory_was_rewritten(self):
        self.ready_tests();p=self.f.root/'tests0';(p/(self.names[0]+'.stderr.log')).unlink();cli.collect(p,p/'artifacts.json')
        with self.assertRaisesRegex(ValueError,'artifacts incomplete'):
            staged.admit_tests(self.f.c,self.f.m,cli.load(self.f.tx/'transaction.json'))
    def test_failed_test_is_preserved_and_stops_later_test_in_that_group(self):
        p=self.testroot/self.names[0];p.write_text(p.read_text().replace('self.assertEqual(2+2,4)','self.fail("injected")'))
        self.f.m['files']=cli.file_records(self.f.pkg,['tests/'+n for n in self.names]);cli.write(self.f.pkg/'gpu-package.json',self.f.m)
        self.begin()
        with self.assertRaisesRegex(ValueError,'incomplete or failed'):self.run_group(0)
        p=self.f.root/'tests0';self.assertTrue((p/'failure.json').is_file());self.assertFalse((p/'result.json').exists())
        self.assertEqual(len(cli.load(p/'cpu-tests.json')),1);self.assertEqual(self.f.calls,[])
    def test_windows_plan_and_test_recipe_require_original_workspace_on_every_host(self):
        f=self.f
        requests={'preflight-plan':dict(gpu_capture=str(f.gpu),group_size='10',test_group_size='2'),
                  'preflight-test-group':dict(transaction=str(f.tx),group_index='0')}
        with patch.object(packet,'is_windows',return_value=True):
            for stage,request in requests.items():
                with self.subTest(stage=stage):
                    with self.assertRaisesRegex(ValueError,'explicit original workspace'):
                        packet.recipe('owned',stage,'cuda',f.root/stage,None,180,request)
                    r=packet.recipe('owned',stage,'cuda',f.root/stage,f.root/'original',180,request)
                    self.assertEqual(r['original_workspace'],str(f.root/'original'))
                    self.assertEqual(r['memory_limit_mb'],2048)
    def test_wrapper_forwards_exact_plan_and_one_group_with_no_gpu_option(self):
        f=self.f;request=dict(gpu_capture=str(f.gpu),group_size='10',test_group_size='2')
        p=packet.recipe('owned','preflight-plan','metal',f.root/'plan-stage',f.root/'original',180,request)
        args=packet.proof_arguments(p);self.assertIn('--test-group-size',args);self.assertEqual(args[-1],'2')
        for value in ('0','01','-1','١',True):
            with self.subTest(value=value),self.assertRaises(ValueError):packet.object_request('preflight-plan',dict(request,test_group_size=value))
        request=dict(transaction=str(f.tx),group_index='1')
        p=packet.recipe('owned','preflight-test-group','metal',f.root/'test-stage',f.root/'original',180,request)
        self.assertEqual(packet.proof_arguments(p),['preflight-test-group','--capture',str(f.root/'test-stage/proof'),'--transaction',str(f.tx),'--group-index','1'])
        r=self.begin();self.assertTrue(packet.verified_staged(r,'preflight-plan','owned'))
        self.assertFalse(packet.verified_staged(dict(r,cpu_tests_verified=True),'preflight-plan','owned'))
        r=self.run_group(0);self.assertTrue(packet.verified_staged(r,'preflight-test-group','owned'))
        self.assertFalse(packet.verified_staged(dict(r,all_cpu_tests_verified=True),'preflight-test-group','owned'))


if __name__=='__main__':unittest.main()
