"""Native suspended launcher contracts with injected WinAPI; no OS child/GPU."""
import importlib.util,json,os,subprocess,sys,tempfile,types,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_native_process import SuspendedNativeProcess


class API:
    STARTF_USESTDHANDLES=0x100;DUPLICATE_SAME_ACCESS=2;WAIT_OBJECT_0=0;WAIT_TIMEOUT=258
    def __init__(self):self.events=[];self.duplicates=[];self.closed=[];self.ended=False;self.code=0;self.fail_create=False;self.fail_duplicate=0
    def GetCurrentProcess(self):return -1
    def DuplicateHandle(self,*args):
        self.events.append(('duplicate',args));self.duplicates.append(300+len(self.duplicates))
        if len(self.duplicates)==self.fail_duplicate:raise OSError('duplicate failure')
        return self.duplicates[-1]
    def CloseHandle(self,handle):self.closed.append(handle)
    def CreateProcess(self,*args):
        self.events.append(('create',args))
        if self.fail_create:raise OSError('create failure')
        return 100,200,123,124
    def WaitForSingleObject(self,handle,milliseconds):
        self.events.append(('wait',handle,milliseconds));return self.WAIT_OBJECT_0 if self.ended else self.WAIT_TIMEOUT
    def GetExitCodeProcess(self,handle):return self.code
    def TerminateProcess(self,handle,code):self.events.append(('terminate',handle,code));self.ended=True;self.code=code


class NativeProcessTests(unittest.TestCase):
    def setUp(self):
        self.api=API();self.resumes=[];self.previous=1
        self.stdout=tempfile.TemporaryFile();self.stderr=tempfile.TemporaryFile();self.addCleanup(self.stdout.close);self.addCleanup(self.stderr.close)
    def process(self,**options):
        defaults=dict(cwd=ROOT,stdin=subprocess.DEVNULL,stdout=self.stdout,stderr=self.stderr,shell=False,creationflags=0x4000,api=self.api,get_handle=lambda fd:fd,startup_factory=lambda:types.SimpleNamespace(dwFlags=0),resume=self.resume)
        defaults.update(options);return SuspendedNativeProcess(['C:\\Python\\python.exe','a b','quote"value'],**defaults)
    def resume(self,handle):self.resumes.append(handle);return self.previous
    def test_creation_is_suspended_below_normal_and_only_stdio_handles_are_inherited(self):
        process=self.process();self.addCleanup(process.close)
        call=[r[1] for r in self.api.events if r[0]=='create'][0]
        self.assertEqual(call[0],'C:\\Python\\python.exe');self.assertTrue(call[4]);self.assertEqual(call[5],0x4004)
        self.assertIsNone(call[6]);self.assertEqual(call[8].lpAttributeList,{'handle_list':self.api.duplicates})
        self.assertEqual([call[8].hStdInput,call[8].hStdOutput,call[8].hStdError],self.api.duplicates)
        self.assertTrue(all(row[1][4] is True for row in self.api.events if row[0]=='duplicate'))
        self.assertCountEqual(self.api.closed,self.api.duplicates);self.assertEqual(self.resumes,[])
        self.assertEqual((process._handle,process.pid,process.thread_id),(100,123,124))
        launch=process.release();self.assertEqual(launch['resume_previous_count'],1);self.assertEqual(launch['creation_flags'],0x4004)
        with self.assertRaisesRegex(RuntimeError,'consumed'):process.release()
        self.assertEqual(self.resumes,[200]);process.terminate();self.assertEqual(process.wait(5),1)
    def test_wrong_suspend_count_never_becomes_a_launch_receipt(self):
        for previous in (0,2,0xffffffff):
            with self.subTest(previous=previous):
                self.previous=previous;process=self.process()
                with self.assertRaisesRegex(RuntimeError,'suspend count'):process.release()
                self.assertFalse(process.resumed);process.terminate();process.wait(5);process.close()
                self.api.ended=False
    def test_missing_containment_can_terminate_without_resuming_and_closes_both_handles(self):
        process=self.process();self.assertIsNone(process.poll());process.terminate();self.assertEqual(process.wait(5),1);process.close();process.close()
        self.assertEqual(self.resumes,[]);self.assertEqual(self.api.closed.count(100),1);self.assertEqual(self.api.closed.count(200),1)
    def test_timeout_and_nonzero_exit_remain_distinct(self):
        process=self.process();self.addCleanup(process.close);process.release()
        with self.assertRaises(subprocess.TimeoutExpired):process.wait(0.001)
        self.api.ended=True;self.api.code=7;self.assertEqual(process.poll(),7);self.assertEqual(process.wait(5),7)
        self.assertFalse(any(r[0]=='terminate' for r in self.api.events))
    def test_creation_and_duplicate_failures_close_only_owned_duplicates(self):
        self.api.fail_create=True
        with self.assertRaisesRegex(OSError,'create failure'):self.process()
        self.assertCountEqual(self.api.closed,self.api.duplicates)
        self.api=API();self.api.fail_duplicate=2
        with self.assertRaisesRegex(OSError,'duplicate failure'):self.process()
        self.assertEqual(self.api.closed,[300]);self.assertFalse(any(r[0]=='create' for r in self.api.events))
    def test_forbidden_flags_or_shell_cannot_create_a_process(self):
        for options in (dict(shell=True),dict(creationflags=0x1004000),dict(stdin=None)):
            with self.subTest(options=options),self.assertRaises(ValueError):self.process(**options)
        self.assertEqual(self.api.events,[])
    def test_wait_budget_is_finite_and_handles_cannot_be_reused_after_close(self):
        process=self.process()
        for timeout in (-1,56,float('inf'),float('nan')):
            with self.subTest(timeout=timeout),self.assertRaises(ValueError):process.wait(timeout)
        process.close()
        with self.assertRaisesRegex(RuntimeError,'closed'):process.poll()
        with self.assertRaisesRegex(RuntimeError,'closed'):process.release()


class NativeSmokeTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('native_smoke_cli_test',ROOT/'scripts/nikke_gpu.py')
        self.cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.cli)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.capture=Path(self.temp.name)
        self.api=API();self.releases=[];self.good_membership=True;self.exit_code=0;self.file_error=None
    def launch(self,argv,**kwargs):
        stdout=kwargs['stdout']
        def resume(handle):
            self.releases.append(handle)
            from test_portable_native_output_probe import Files
            import portable_native_output_probe as probe
            files=Files();files.fail=self.file_error;record=probe.probe(Path(argv[-1]),dll=files,get_error=lambda:files.error)
            stdout.write(json.dumps(record).encode());stdout.flush();self.api.ended=True;self.api.code=self.exit_code if record['status']=='verified' else 71;return 1
        return SuspendedNativeProcess(argv,**kwargs,api=self.api,get_handle=lambda fd:fd,startup_factory=lambda:types.SimpleNamespace(dwFlags=0),resume=resume)
    def snapshot(self,process):
        self.assertEqual(self.releases,[])
        return dict(wrapper_pid=os.getpid(),child_pid=process.pid,child_ppid=os.getpid(),child_creation_filetime_ticks='123',parent_observation='os_process_snapshot',job_members=[os.getpid(),process.pid] if self.good_membership else [os.getpid()],job_memory_limit_bytes=2147483648)
    def proof(self):
        import portable_native_process as native
        import portable_offline_assembler as assembler
        with patch.object(native,'SuspendedNativeProcess',self.launch),patch.object(assembler,'inspect_process',self.snapshot):self.cli.native_smoke_child(self.capture)
    def test_existing_smoke_exercises_same_native_gate_without_compiler_or_gpu(self):
        self.proof();self.assertTrue(self.cli.audit_native_smoke(self.capture,os.getpid()))
        self.assertEqual(self.releases,[200]);self.assertIn(100,self.api.closed);self.assertIn(200,self.api.closed)
        record=self.cli.load(self.capture/'native-smoke.json');self.assertEqual(record['argv'][1:3],['-I','-S']);self.assertEqual(Path(record['argv'][3]).name,'portable_native_output_probe.py');self.assertEqual(record['gpu_calls'],0)
        path=self.capture/'native-smoke.json';record['native_launch']['resume_previous_count']=0;self.cli.write(path,record)
        with self.assertRaisesRegex(ValueError,'launch gate'):self.cli.audit_native_smoke(self.capture,os.getpid())
        record['native_launch']['resume_previous_count']=1;self.cli.write(path,record)
        (self.capture/'native-smoke.stdout.log').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'output mismatch'):self.cli.audit_native_smoke(self.capture,os.getpid())
    def test_failed_file_creation_retains_actual_win32_error_and_native_return(self):
        self.file_error='CreateFileW'
        with self.assertRaisesRegex(RuntimeError,'output probe failed'):self.proof()
        record=self.cli.load(self.capture/'native-smoke.json');self.assertEqual(record['return_code'],71)
        self.assertEqual(record['output_probe']['winerror'],5);self.assertEqual(record['output_probe']['failed_operation'],'CreateFileW')
        self.assertEqual(self.releases,[200]);self.assertIn(100,self.api.closed)
        with self.assertRaisesRegex(ValueError,'command/return'):self.cli.audit_native_smoke(self.capture,os.getpid())
    def test_native_smoke_refuses_bad_membership_without_resuming(self):
        self.good_membership=False
        with self.assertRaisesRegex(RuntimeError,'not in the validation Job'):self.proof()
        self.assertEqual(self.releases,[]);self.assertTrue(self.api.ended);self.assertFalse((self.capture/'native-smoke.json').exists())
        rows=[json.loads(line) for line in (self.capture/'native-smoke-phases.jsonl').read_text().splitlines()]
        self.assertEqual(rows[0]['state'],'rejected');self.assertIn(100,self.api.closed)
    def test_smoke_nonzero_exit_or_output_corruption_is_not_success(self):
        self.exit_code=7
        with self.assertRaisesRegex(RuntimeError,'output probe failed'):self.proof()
        self.assertEqual(self.cli.load(self.capture/'native-smoke.json')['return_code'],7);self.assertEqual(self.releases,[200])
        self.assertFalse(any(r[0]=='terminate' for r in self.api.events))


if __name__=='__main__':unittest.main()
