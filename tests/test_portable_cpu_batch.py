"""Actual selected-test discovery plus parent failure gates; CPU/GPU separated."""
import importlib.util,json,os,subprocess,sys,tempfile,types,unittest,uuid
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_cpu_tests import run_groups,complete,validate_groups,validate_dependency_files,AUDIT_FILES
s=importlib.util.spec_from_file_location('batch_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)

class CPUGroupTests(unittest.TestCase):
    def test_named_capacity_policy_source_audit_requires_its_pinned_document(self):
        pattern='test_effect_target_count_policy.py'
        for name in AUDIT_FILES[pattern]:
            if name.endswith('IMPL-STATUS.md'):continue
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
        with self.assertRaisesRegex(ValueError,'IMPL-STATUS.md'):
            validate_dependency_files(self.root,[pattern])
    def test_audit_dependency_is_checked_before_worker_and_requires_manifest_record(self):
        pattern='test_coordinate_physical_frontier.py';(self.root/'tests'/pattern).write_text('# never imported')
        with self.assertRaisesRegex(ValueError,'CPU audit dependency missing'):self.run_groups([pattern])
        self.assertFalse((self.capture/'cpu-tests.json').exists())
        for name in AUDIT_FILES[pattern]:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
        validate_groups(self.root,[pattern])
        with self.assertRaisesRegex(ValueError,'immutable payload'):validate_dependency_files(self.root,[pattern],included=set())
        validate_dependency_files(self.root,[pattern],included=set(AUDIT_FILES[pattern]))
    def test_new_mixed_data_dependency_blocks_before_test_import(self):
        pattern='test_coordinate_mixed.py';(self.root/'tests'/pattern).write_text('raise AssertionError("must not import")')
        with self.assertRaisesRegex(ValueError,'CPU audit dependency missing'):self.run_groups([pattern])
        self.assertFalse((self.capture/'cpu-tests.json').exists())
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve();(self.root/'tests').mkdir();self.capture=self.root/'capture';self.capture.mkdir();self.names=[]
        self.addCleanup(self.clear_modules)
    def clear_modules(self):
        for n in self.names:sys.modules.pop(n[:-3],None)
    def module(self,body):
        name='test_portable_batch_'+uuid.uuid4().hex+'.py';(self.root/'tests'/name).write_text(body);self.names.append(name);return name
    def run_groups(self,patterns):return run_groups(self.root,self.capture,patterns,cli.write)
    def test_execution_cache_flags_do_not_leak_into_unit_workers(self):
        with patch.dict(os.environ,NIKKE_SLANG_GENERATION_CACHE='/selected/cache',NIKKE_SLANG_GENERATION_REQUIRED='1'):
            tests=cli.cpu_test_environment(self.capture);execution=cli.validation_environment(self.capture)
            for key in ('NIKKE_SLANG_GENERATION_CACHE','NIKKE_SLANG_GENERATION_REQUIRED'):
                self.assertNotIn(key,tests);self.assertEqual(execution[key],os.environ[key])

    def test_all_selected_groups_run_once_in_order_with_one_pid_and_logs(self):
        a=self.module("import unittest\nprint('import-first')\nclass A(unittest.TestCase):\n def test_a(self):print('first');self.assertTrue(True)\n")
        b=self.module("import unittest\nclass B(unittest.TestCase):\n def test_b(self):print('second');self.assertEqual(2+3,5)\n")
        before=list(sys.path);rows=self.run_groups([a,b]);self.assertEqual(sys.path,before)
        self.assertTrue(complete(rows,[a,b]));self.assertEqual([r['tests'] for r in rows],[1,1]);self.assertEqual({r['runner_pid'] for r in rows},{os.getpid()})
        self.assertEqual(cli.load(self.capture/'cpu-tests.json'),rows);self.assertIn('import-first',(self.capture/(a+'.stdout.log')).read_text());self.assertIn('Ran 1 test',(self.capture/(b+'.stderr.log')).read_text())
        with self.assertRaises(FileExistsError):self.run_groups([a,b])
    def test_failure_stops_later_group_and_keeps_failure_trace(self):
        a=self.module("import unittest\nclass A(unittest.TestCase):\n def test_a(self):self.fail('literal-failure')\n")
        b=self.module("raise AssertionError('later group must not import')\n")
        rows=self.run_groups([a,b]);self.assertFalse(complete(rows,[a,b]));self.assertEqual(len(rows),1);self.assertEqual(rows[0]['failures'],1);self.assertIn('literal-failure',(self.capture/(a+'.stderr.log')).read_text());self.assertFalse((self.capture/(b+'.stderr.log')).exists())
    def test_zero_discovery_and_import_error_cannot_pass(self):
        for source in ('# no tests\n',"raise RuntimeError('failed import')\n"):
            name=self.module(source);target=self.root/('capture-'+uuid.uuid4().hex);target.mkdir()
            rows=run_groups(self.root,target,[name],cli.write);self.assertFalse(complete(rows,[name]));self.assertEqual(rows[0]['exit_code'],1)
    def test_all_paths_validated_before_any_discovery(self):
        name=self.module("raise AssertionError('must not import')\n")
        for patterns in ([name,'missing.py'],[name,name],['../test_unsafe.py']):
            with self.subTest(patterns=patterns),self.assertRaises(ValueError):self.run_groups(patterns)
            self.assertFalse((self.capture/(name+'.stderr.log')).exists())
    def test_receipt_cannot_omit_reorder_fail_or_claim_zero_tests(self):
        good=[dict(pattern='test_a.py',exit_code=0,tests=1,failures=0,errors=0)]
        self.assertTrue(complete(good,['test_a.py']))
        for rows in ([],[dict(good[0],pattern='test_b.py')],[dict(good[0],exit_code=1)],[dict(good[0],tests=0)],[dict(good[0],errors=1)]):self.assertFalse(complete(rows,['test_a.py']))

class CPUParentTests(unittest.TestCase):
    def test_suite_cpu_budget_is_bounded_recorded_and_separate_from_gpu(self):
        self.capture.mkdir()
        def child(*args,**kwargs):
            self.assertEqual(kwargs['timeout'],90)
            cli.write(self.capture/'cpu-tests.json',[dict(pattern=self.pattern,exit_code=0,tests=1,failures=0,errors=0)])
            return types.SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
        with self.context(),patch.object(cli.subprocess,'run',side_effect=child),patch.object(cli,'run_job') as job:
            cli.SUITES['fixture']['cpu_test_timeout']=90
            self.assertEqual(len(cli.cpu_test_groups(self.m,self.capture)),1);job.assert_not_called()
        self.assertEqual(cli.load(self.capture/'cpu-batch.json')['timeout_seconds'],90)
        for value in (0,-1,181,True,1.5,'90'):
            with self.context(),patch.object(cli.subprocess,'run') as run:
                cli.SUITES['fixture']['cpu_test_timeout']=value
                with self.assertRaisesRegex(ValueError,'bounded CPU'):cli.cpu_test_groups(self.m,self.capture)
                run.assert_not_called()
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);(self.root/'tests').mkdir();self.pattern='test_literal.py';(self.root/'tests'/self.pattern).write_text('# parent fixture')
        self.m=dict(suite='fixture',package_id='fixture',purpose='sealed');self.capture=self.root/'capture'
    def context(self):
        import contextlib
        # These synthetic suites isolate CPU failure/timeout gates and have no
        # adapter. Exercise the real storage gate in its dedicated tests.
        s=contextlib.ExitStack();s.enter_context(patch.object(cli,'capture_storage_preflight'));s.enter_context(patch.object(cli,'ROOT',self.root));s.enter_context(patch.object(cli,'SUITES',dict(fixture=dict(tests=[self.pattern]))));s.enter_context(patch.object(cli,'verify_package',return_value=self.m));s.enter_context(patch.object(cli,'cpu_preflight',return_value=dict(passed=True)));s.enter_context(patch.object(cli,'os',types.SimpleNamespace(**dict(vars(os),name='nt'))));return s
    def test_shared_smoke_budget_is_separate_from_the_default_unit_budget(self):
        for smoke,timeout in ((False,60),(True,180)):
            self.capture=self.root/('shared-smoke' if smoke else 'suite-tests');self.capture.mkdir()
            def child(*args,**kwargs):
                cli.write(self.capture/'cpu-tests.json',[dict(pattern=self.pattern,exit_code=0,tests=1,failures=0,errors=0)])
                return types.SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
            with self.context(),patch.object(cli,'SMOKE_TESTS',[self.pattern]),patch.object(cli.subprocess,'run',side_effect=child) as run:
                rows=cli.cpu_test_groups(self.m,self.capture,smoke=smoke)
            self.assertEqual(len(rows),1);self.assertEqual(run.call_args.kwargs['timeout'],timeout)
            receipt=cli.load(self.capture/'cpu-batch.json');self.assertEqual(receipt['timeout_seconds'],timeout)
            self.assertEqual(receipt['timeout_policy'],'shared-smoke' if smoke else 'suite-unit-tests');self.assertEqual(receipt['gpu_calls'],0)
    def test_failed_unit_gate_skips_full_native_battles_and_gpu(self):
        with self.context(),patch.object(cli,'cpu_test_groups',side_effect=ValueError('test payload absent')),patch.object(cli,'cpu_preflight') as native,patch.object(cli,'run_job') as job,self.assertRaisesRegex(ValueError,'test payload absent'):
            cli.run_capture(self.capture,'cuda',60,cpu_only=True)
        native.assert_not_called();job.assert_not_called();self.assertFalse((self.capture/'cpu.json').exists());self.assertFalse((self.root/'gpu-claimed-cuda.json').exists())
    def test_successful_units_still_require_native_gate_before_cpu_only_success(self):
        order=[]
        def units(*a,**k):order.append('units')
        def native(*a,**k):order.append('native');return dict(passed=True,gpu_calls=0)
        with self.context(),patch.object(cli,'cpu_test_groups',side_effect=units),patch.object(cli,'cpu_preflight',side_effect=native),patch.object(cli,'run_job') as job:
            result=cli.run_capture(self.capture,'cuda',60,cpu_only=True)
        self.assertEqual(order,['units','native']);self.assertTrue(result['cpu_verified']);self.assertEqual(cli.load(self.capture/'cpu.json'),dict(passed=True,gpu_calls=0));job.assert_not_called()
    def test_incomplete_successful_child_and_failed_child_never_claim_gpu(self):
        for mode in ('missing_receipt','zero_tests','failed'):
            self.capture=self.root/mode
            def child(*args,**kwargs):
                if mode!='missing_receipt':cli.write(self.capture/'cpu-tests.json',[dict(pattern=self.pattern,exit_code=1 if mode=='failed' else 0,tests=0 if mode=='zero_tests' else 1,failures=1 if mode=='failed' else 0,errors=0)])
                return types.SimpleNamespace(returncode=1 if mode=='failed' else 0,stdout=b'batch stdout',stderr=b'batch stderr')
            with self.context(),patch.object(cli.subprocess,'run',side_effect=child) as run,patch.object(cli,'run_job') as job,self.assertRaisesRegex(ValueError,'CPU tests failed'):
                cli.run_capture(self.capture,'cuda',60)
            run.assert_called_once();job.assert_not_called();self.assertFalse((self.root/'gpu-claimed-cuda.json').exists());self.assertEqual((self.capture/'cpu-batch.stdout.log').read_bytes(),b'batch stdout');self.assertEqual(cli.load(self.capture/'cpu-batch.json')['gpu_calls'],0)
    def test_timeout_keeps_partial_logs_and_blocks_gpu(self):
        with self.context(),patch.object(cli.subprocess,'run',side_effect=subprocess.TimeoutExpired(['worker'],60,output=b'partial out',stderr=b'partial err')),patch.object(cli,'run_job') as job,self.assertRaises(subprocess.TimeoutExpired):cli.run_capture(self.capture,'cuda',60)
        job.assert_not_called();self.assertFalse((self.root/'gpu-claimed-cuda.json').exists());self.assertEqual((self.capture/'cpu-batch.stderr.log').read_bytes(),b'partial err');self.assertTrue(cli.load(self.capture/'cpu-batch.json')['timed_out']);self.assertEqual(cli.load(self.capture/'cpu-batch.json')['timeout_seconds'],60)

if __name__=='__main__':unittest.main()
