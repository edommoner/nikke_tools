"""Fresh native gates are complete before GPU; no native values cross stages."""
import contextlib,copy,importlib.util,json,os,shutil,struct,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_staged_preflight as flow
s=importlib.util.spec_from_file_location('staged_flow_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
s=importlib.util.spec_from_file_location('staged_flow_packet',ROOT/'scripts/run-gpu-packet.py');packet=importlib.util.module_from_spec(s);s.loader.exec_module(packet)


class StagedPreflightTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.pkg=self.root/'packet';self.pkg.mkdir();self.tx=self.root/'begin';self.gpu=self.root/'gpu'
        self.domains=[dict(arg=1),None,dict(arg=3)];self.data=struct.pack('<IIII',3,11,22,33)
        self.digest=lambda v:cli.sha(json.dumps(v,sort_keys=True).encode())
        self.value=lambda d:dict(answer=d['arg']*3,private_native_payload='must-never-be-written') if d is not None else dict(status=64)
        self.rows=[('case'+str(i),[w],d) for i,(w,d) in enumerate(zip((11,22,33),self.domains,strict=True))]
        self.m=dict(package_id='owned',suite='fixture',purpose='sealed',golden=dict(source_sha256={},input_sha256=cli.sha(self.data),
            output_sha256=cli.sha(struct.pack('<III',3,64,9)),entries=[dict(name=n,input_sha256=cli.sha(self.data[4+i*4:8+i*4]),native_sha256=self.digest(self.value(d))) for i,(n,_,d) in enumerate(self.rows)]))
        cli.write(self.pkg/'gpu-package.json',self.m);self.calls=[]
        self.adapter=SimpleNamespace(suite=SimpleNamespace(INPUT=1),cross=SimpleNamespace(digest=self.digest))
        def native(a,d):self.calls.append(copy.deepcopy(d));return self.value(d)
        def tests(m,c):
            rows=[dict(pattern='test_owned.py',tests=1,exit_code=0,failures=0,errors=0,skipped=0)];cli.write(c/'cpu-tests.json',rows);return rows
        self.c=SimpleNamespace(ROOT=self.pkg,verify_package=lambda p:self.m,is_development=lambda m:False,compiler_only=lambda m:False,
            SUITES={'fixture':dict(native=2,tests=['test_owned.py'],output_words=1)},cpu_test_groups=tests,
            open_suite=lambda m:self.adapter,prepare_entries=lambda a,m:(self.rows,self.data),native_value=native,
            sha=cli.sha,write=cli.write,load=cli.load,file_records=cli.file_records,check_records=cli.check_records,
            transport_input_receipt=cli.transport_input_receipt,publish_transport_input=cli.publish_transport_input,
            collect=cli.collect,forbid_gpu=cli.forbid_gpu,audit_generation_capture=lambda *a:None,environment_preserved=lambda *a:None,capture_storage_preflight=lambda *a:None)
        self.host_patch=patch.object(flow,'host',return_value=dict(platform='fixture',python_sha256='pinned'));self.host_patch.start();self.addCleanup(self.host_patch.stop)
        self.os_patch=patch.object(flow,'os',SimpleNamespace(name='posix',fsync=os.fsync,getpid=os.getpid));self.os_patch.start();self.addCleanup(self.os_patch.stop)
    def begin(self):return flow.begin(self.c,self.tx,'metal',self.gpu,2)
    def groups(self):
        for i in (0,1):
            proxy=SimpleNamespace(name='posix',fsync=os.fsync,getpid=lambda i=i:1000+i)
            with patch.object(flow,'os',proxy):flow.group(self.c,self.tx,i,self.root/('group'+str(i)))
    def ready(self):self.begin();self.groups();return flow.admit(self.c,self.m,self.tx,'metal',self.gpu)
    def gpu_input(self):
        self.ready();self.gpu.mkdir();flow.prepare_gpu_input(self.c,self.m,self.tx,self.gpu,'metal');flow.claim_execution(self.c,self.tx,self.gpu)
        cli.write(self.gpu/'run.json',dict(mode='staged-gpu',backend='metal',input_protocol=flow.PROTOCOL))
    def test_begin_runs_tests_and_static_input_without_oracles_or_gpu(self):
        r=self.begin();self.assertTrue(r['transaction_ready']);self.assertEqual(self.calls,[])
        self.assertEqual((self.tx/'input.bin').read_bytes(),self.data);self.assertFalse((self.tx/'cpu.json').exists())
        with self.assertRaises(FileExistsError):flow.begin(self.c,self.root/'another','metal',self.root/'gpu2',2)
    def test_every_case_fresh_once_and_receipts_contain_no_native_values(self):
        r=self.ready();self.assertTrue(r['all_native_preflight_verified']);self.assertFalse(r['calculation_verified'])
        self.assertEqual((r['input_count'],r['native_cases'],r['groups']),(3,2,2));self.assertEqual(self.calls,self.domains)
        for i in (0,1):
            text=(self.root/('group'+str(i))/'result.json').read_text();self.assertNotIn('must-never-be-written',text);self.assertNotIn('private_native_payload',text)
        before=list(self.calls);flow.admit(self.c,self.m,self.tx,'metal',self.gpu);self.assertEqual(before,self.calls)
    def test_missing_group_reused_child_and_replayed_group_are_rejected(self):
        self.begin()
        with self.assertRaises(FileNotFoundError):flow.admit(self.c,self.m,self.tx,'metal',self.gpu)
        self.groups()
        with self.assertRaises(FileExistsError):flow.group(self.c,self.tx,0,self.root/'replay')
        proof=self.root/'group1';row=cli.load(proof/'result.json');row['child_pid']=1000;cli.write(proof/'result.json',row);cli.collect(proof,proof/'artifacts.json')
        with self.assertRaisesRegex(ValueError,'identity/scope'):flow.admit(self.c,self.m,self.tx,'metal',self.gpu)
    def test_source_host_transaction_and_gpu_capture_binding_cannot_drift(self):
        self.begin();original=(self.pkg/'gpu-package.json').read_bytes();(self.pkg/'gpu-package.json').write_bytes(original+b' ')
        with self.assertRaisesRegex(ValueError,'identity/source/host'):flow.context(self.c,self.tx)
        (self.pkg/'gpu-package.json').write_bytes(original)
        with patch.object(flow,'host',return_value=dict(platform='other')),self.assertRaises(ValueError):flow.context(self.c,self.tx)
        with self.assertRaises(ValueError):flow.context(self.c,self.tx,gpu_capture=self.root/'different')
        other=self.root/'copied';shutil.copytree(self.tx,other)
        with self.assertRaises(ValueError):flow.context(self.c,other)
    def test_wrong_native_or_mutated_domain_never_publishes_success(self):
        self.begin();self.c.native_value=lambda a,d:dict(wrong=True)
        with self.assertRaisesRegex(ValueError,'fingerprint/domain'):flow.group(self.c,self.tx,0,self.root/'bad')
        self.assertFalse((self.root/'bad/result.json').exists());self.assertTrue((self.root/'bad/failure.json').exists())
        self.assertFalse((self.tx/'gpu-execution-claimed.json').exists())
        def changed(a,d):
            value=self.value(d);d['mutated']=True;return value
        self.c.native_value=changed
        with self.assertRaisesRegex(ValueError,'fingerprint/domain'):flow.group(self.c,self.tx,1,self.root/'mutated')
        self.assertFalse((self.root/'mutated/result.json').exists())
    def test_prepared_gpu_input_is_static_and_has_a_distinct_gate(self):
        self.gpu_input();before=list(self.calls)
        self.assertEqual(flow.read_gpu_input(self.c,self.m,self.gpu),(self.data,1));self.assertEqual(self.calls,before)
        self.assertFalse((self.gpu/'cpu.json').exists());self.assertTrue((self.gpu/'staged-preflight.json').exists())
        with self.assertRaises(FileExistsError):flow.claim_execution(self.c,self.tx,self.gpu)
        (self.gpu/'input.bin').write_bytes(self.data[:-1]+b'x')
        with self.assertRaises(ValueError):flow.read_gpu_input(self.c,self.m,self.gpu)
    def test_dispatch_and_matching_hash_still_require_independent_native_audit(self):
        self.gpu_input();raw=struct.pack('<III',3,64,9);(self.gpu/'readback.bin').write_bytes(raw)
        cli.write(self.gpu/'evidence.json',dict(backend='metal',gpu_execution_verified=True,source_sha256={},output_sha256=cli.sha(raw),transport=dict(command_status='completed',cases=3)))
        result=flow.finish_gpu(self.c,self.m,self.gpu,dict(passed=True),'metal')
        self.assertTrue(result['gpu_execution_completed']);self.assertTrue(result['readback_fingerprint_matches'])
        self.assertFalse(result['calculation_verified']);self.assertTrue(result['pending_native_audit']);self.assertFalse(result['passed'])
        (self.gpu/'readback.bin').write_bytes(b'wrong')
        self.assertFalse(flow.finish_gpu(self.c,self.m,self.gpu,dict(passed=True),'metal')['readback_fingerprint_matches'])
    def test_bounded_stage_requests_and_gpu_budget_are_not_interchangeable(self):
        for name,request in (('preflight-begin',dict(gpu_capture=str(self.gpu),group_size='2')),
            ('preflight-native-group',dict(transaction=str(self.tx),group_index='0')),
            ('staged-gpu-linked',dict(transaction=str(self.tx),linked_package=str(self.root/'compiler'),linked_capture=str(self.root/'link')))):
            p=packet.recipe('owned',name,'cuda',self.root/name,self.root/'original',180,request);args=packet.proof_arguments(p)
            self.assertEqual(p['memory_limit_mb'],2048)
            if name=='staged-gpu-linked':self.assertIn('60',args);self.assertNotIn('--require-cache',args)
            else:self.assertNotIn('run',args)
            with self.assertRaises(ValueError):packet.object_request(name,dict(request,extra='--gpu'))
        with self.assertRaises(ValueError):packet.recipe('owned','staged-gpu-linked','metal',self.root/'out',self.root/'original',180,dict(transaction=str(self.tx),linked_package='/compiler',linked_capture='/link'))
    def test_staged_protocol_cannot_be_selected_by_an_ordinary_run(self):
        cli.write(self.gpu.with_suffix('.json'),{})
        self.gpu.mkdir();cli.write(self.gpu/'run.json',dict(mode='gpu',input_protocol=flow.PROTOCOL))
        with self.assertRaisesRegex(ValueError,'explicit staged'):cli.read_prepared_transport_input(self.m,self.gpu)
    def test_windows_gate_requires_terminal_job_and_preserves_unknown_service(self):
        self.begin();outer=self.root/'windows-stage';proof=outer/'proof';shutil.copytree(self.tx,proof)
        plan=packet.recipe('owned','preflight-begin','cuda',outer,self.root/'original',180,dict(gpu_capture=str(self.gpu),group_size='2'))
        cli.write(outer/'recipe.json',plan);cli.write(outer/'job.json',dict(records=[]));self.c.module=lambda _:packet
        facts=dict(timeout_seconds=179.5,passed=True,timed_out=False,child_exit_code=0,final_child_exit_code=0,below_normal_priority=True,error=None,cleanup_error=None,observation_error=None)
        cli.write(outer/'execution.json',facts);comparison=dict(missing_existing_processes=[])
        cli.write(outer/'observation.json',dict(before={},after={},comparison=comparison))
        self.c.job_contained=lambda *a,**k:(True,1000);self.c.environment_preserved=lambda *a:False
        with patch.object(flow,'os',SimpleNamespace(name='nt')),patch('windows_validation_observer.compare_snapshots',return_value=comparison):
            result=flow.terminal_cpu_stage(self.c,proof,self.m,'preflight-begin')
            self.assertTrue(result['containment_verified']);self.assertFalse(result['preservation_verified'])
            for key,value in (('timed_out',True),('passed',False),('child_exit_code',2),('below_normal_priority',False),('cleanup_error','unknown')):
                cli.write(outer/'execution.json',dict(facts,**{key:value}))
                with self.subTest(key=key),self.assertRaises(ValueError):flow.terminal_cpu_stage(self.c,proof,self.m,'preflight-begin')
            cli.write(outer/'execution.json',facts);self.c.job_contained=lambda *a,**k:(False,None)
            with self.assertRaises(ValueError):flow.terminal_cpu_stage(self.c,proof,self.m,'preflight-begin')
    def run_context(self,job):
        stack=contextlib.ExitStack();compiler=self.root/'sdk';(compiler/'bin').mkdir(exist_ok=True,parents=True)
        (compiler/'bin'/('slangc.exe' if os.name=='nt' else 'slangc')).write_bytes(b'fixture SDK; never execute')
        stack.enter_context(patch.dict(os.environ,NIKKE_SLANG_ROOT=str(compiler)))
        for name,value in (('ROOT',self.pkg),('SUITES',self.c.SUITES),('verify_package',lambda _:self.m),('open_suite',self.c.open_suite),
            ('prepare_entries',self.c.prepare_entries),('run_job',job),('copy_generated',lambda *a,**k:None),
            ('validate_generation_request',lambda *a:None),('capture_storage_preflight',lambda *a,**k:None),
            ('required_generation_cache_preflight',lambda *a:None),('metal_device_preflight',lambda *a:None)):
            stack.enter_context(patch.object(cli,name,value))
        stack.enter_context(patch('portable_wire_layout.check_metal',return_value={}))
        return stack
    def test_run_cannot_launch_before_all_native_groups_or_invoke_normal_preflight(self):
        self.begin();calls=[]
        with (self.run_context(lambda *a,**k:calls.append('GPU')),patch.object(cli,'cpu_preflight',side_effect=AssertionError('Staged run must not masquerade as a normal gate')),
            self.assertRaises(FileNotFoundError)):
            cli.run_capture(self.gpu,'metal',60,preflight_transaction=self.tx)
        self.assertEqual(calls,[]);self.assertFalse((self.tx/'gpu-execution-claimed.json').exists())
    def test_run_records_pending_audit_without_fabricating_cpu_json(self):
        self.ready();calls=[]
        def job(capture,*a,**k):
            calls.append('GPU mock');raw=struct.pack('<III',3,64,9);(capture/'readback.bin').write_bytes(raw)
            cli.write(capture/'evidence.json',dict(backend='metal',gpu_execution_verified=True,source_sha256={},output_sha256=cli.sha(raw),transport=dict(command_status='completed',cases=3)))
            return dict(passed=True)
        with self.run_context(job),patch.object(cli,'cpu_preflight',side_effect=AssertionError('No normal gate substitution')),patch.object(cli,'audit_capture',side_effect=AssertionError('Defer independent native audit')):
            r=cli.run_capture(self.gpu,'metal',60,preflight_transaction=self.tx)
        self.assertEqual(calls,['GPU mock']);self.assertFalse(r['calculation_verified']);self.assertTrue(r['pending_native_audit'])
        self.assertFalse((self.gpu/'cpu.json').exists());self.assertEqual(cli.load(self.gpu/'run.json')['status'],'awaiting-native-audit')
    def test_ordinary_run_still_executes_ordinary_preflight_and_cannot_reuse_transaction(self):
        self.begin();gpu=[]
        with (self.run_context(lambda *a,**k:gpu.append(1)),patch.object(cli,'cpu_test_groups',return_value=[]) as tests,
            patch.object(cli,'cpu_preflight',return_value=dict(passed=True)) as native,self.assertRaises(FileExistsError)):
            cli.run_capture(self.root/'ordinary','metal',60)
        self.assertEqual(tests.call_count,1);self.assertEqual(native.call_count,1);self.assertEqual(gpu,[])


if __name__=='__main__':unittest.main()
