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


    def split_begin(self):
        name=self.names[1];p=self.testroot/name
        p.write_text('import unittest\nclass TestOwned(unittest.TestCase):\n @classmethod\n def setUpClass(cls):cls.entered=True\n'+''.join(' def test_'+str(i)+'(self):self.assertTrue(self.entered)\n' for i in range(5)))
        self.f.m['files']=cli.file_records(self.f.pkg,['tests/'+n for n in self.names]);cli.write(self.f.pkg/'gpu-package.json',self.f.m)
        return flow.begin(self.f.c,self.f.tx,'metal',self.f.gpu,2,test_group_size=1,split_test_pattern=name,test_case_group_size=2)
    def test_case_plan_discovers_without_fixtures_and_executes_every_original_id(self):
        self.split_begin();c=cli.load(self.f.tx/'transaction.json');name=self.names[1]
        module=sys.modules[name[:-3]];self.assertFalse(hasattr(module.TestOwned,'entered'))
        self.assertEqual(c['test_groups'],[[self.names[0]],[name],[name],[name],[self.names[2]]])
        ids=[case.id() for case in worker.discovered_cases(self.f.pkg,name)]
        self.assertEqual(c['test_case_groups'],[None,{name:ids[:2]},{name:ids[2:4]},{name:ids[4:]},None])
        for index in range(5):self.run_group(index)
        stages=staged.admit_tests(self.f.c,self.f.m,c);self.assertEqual(len(stages),5)
        rows=[row for index in range(5) for row in cli.load(self.f.root/('tests'+str(index))/'cpu-tests.json')]
        self.assertEqual(sum(r['tests'] for r in rows),7)
        self.assertEqual([v for r in rows for v in r.get('case_ids',[])],ids)
        self.assertEqual(self.f.calls,[])
    def test_case_plan_rejects_missing_duplicated_reordered_or_partial_ids(self):
        self.split_begin();c=cli.load(self.f.tx/'transaction.json');name=self.names[1]
        for change in ('missing','duplicate','reverse','partial','unknown'):
            bad=copy.deepcopy(c)
            if change=='partial':del bad['test_case_group_size']
            elif change=='unknown':bad['split_test_pattern']='test_unknown.py'
            else:
                ids=bad['test_case_groups'][1][name]
                if change=='missing':ids.pop()
                elif change=='duplicate':ids.append(ids[0])
                else:ids.reverse()
            with self.subTest(change=change),self.assertRaises(ValueError):staged.validate_plan(self.f.c,self.f.m,bad)
        for size in (0,True,3):
            with self.subTest(size=size),self.assertRaises(ValueError):staged.case_plan(self.f.c,self.f.m,size,name,2)
    def test_selected_receipts_cannot_admit_partial_or_forged_ids(self):
        self.split_begin();c=cli.load(self.f.tx/'transaction.json');name=self.names[1]
        for index in range(5):self.run_group(index)
        p=self.f.root/'tests1';original=cli.load(p/'cpu-tests.json')
        for change in ('missing','duplicate','reverse','no_ids','count'):
            rows=copy.deepcopy(original)
            if change=='missing':rows[0]['case_ids'].pop()
            elif change=='duplicate':rows[0]['case_ids'].append(rows[0]['case_ids'][0])
            elif change=='reverse':rows[0]['case_ids'].reverse()
            elif change=='no_ids':del rows[0]['case_ids']
            else:rows[0]['tests']-=1
            cli.write(p/'cpu-tests.json',rows);cli.collect(p,p/'artifacts.json')
            with self.subTest(change=change),self.assertRaises(ValueError):staged.admit_tests(self.f.c,self.f.m,c)
        cli.write(p/'cpu-tests.json',original);result=cli.load(p/'result.json');result['selected_cases'][name].reverse();cli.write(p/'result.json',result);cli.collect(p,p/'artifacts.json')
        with self.assertRaises(ValueError):staged.admit_tests(self.f.c,self.f.m,c)
    def test_case_wrapper_requires_exact_optional_pair_and_canonical_size(self):
        request=dict(gpu_capture=str(self.f.gpu),group_size='10',test_group_size='1',split_test_pattern=self.names[1],test_case_group_size='3')
        p=packet.recipe('owned','preflight-plan','cuda',self.f.root/'split',self.f.root/'original',180,request)
        args=packet.proof_arguments(p)
        self.assertEqual(args[-4:],['--split-test-pattern',self.names[1],'--test-case-group-size','3'])
        self.assertEqual(p['memory_limit_mb'],2048)
        for key in ('split_test_pattern','test_case_group_size'):
            bad=dict(request);del bad[key]
            with self.subTest(key=key),self.assertRaises(ValueError):packet.object_request('preflight-plan',bad)
        for value in ('0','01',True,'-1','65537'):
            with self.subTest(value=value),self.assertRaises(ValueError):packet.object_request('preflight-plan',dict(request,test_case_group_size=value))
        for value in ('../test_x.py','/test_x.py','test_x.py --gpu'):
            with self.subTest(value=value),self.assertRaises(ValueError):packet.object_request('preflight-plan',dict(request,split_test_pattern=value))


if __name__=='__main__':unittest.main()
