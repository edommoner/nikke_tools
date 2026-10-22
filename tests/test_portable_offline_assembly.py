"""Fault-inject the offline producer chain, process gate and audit; no real exe/GPU."""
import contextlib,copy,ctypes as C,json,os,subprocess,sys,time,types,unittest
from pathlib import Path
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_backend as backend
import portable_offline_assembler as assembler
import test_portable_compile_cli as producer_test
from windows_validation_observer import compare_snapshots
cli=producer_test.cli
PTX=b'.version 8.4\n.target sm_86\n.address_size 64\n.visible .entry portableEvents() { ret; }\n'
ELF=b'\x7fELF'+b'fake deterministic cubin'.ljust(80,b'\0')

class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.base=producer_test.CompileCLITests();self.base.setUp();self.addCleanup(self.base.doCleanups)
        self.root=self.base.root;self.producer=self.base.capture;self.source_package=self.root/'source-package';self.source_package.mkdir()
        self.package=self.root/'new-package';self.package.mkdir();self.capture=self.root/'assembly';self.capture.mkdir()
        self.m=copy.deepcopy(self.base.m);self.m['package_id']='new-fixture'
        cli.write(self.source_package/'gpu-package.json',self.base.m);cli.write(self.package/'gpu-package.json',self.m)
        self.tool=self.root/'ptxas.exe';self.tool.write_bytes(b'MZpinned test compiler');self.tool_sha=assembler.digest(self.tool.read_bytes())
        self.return_code=0;self.payload=ELF;self.fail_wait=False;self.processes=[]
        self.base.native.payload=PTX
        def compile_ptx(source):
            native=backend.C.WinDLL('nvrtc64_dummy.dll')
            artifact,receipt=backend.compile_cuda_artifact(native,source.read_bytes(),[self.base.dll],artifact_kind='ptx')
            source.with_suffix('.ptx').write_bytes(artifact);return artifact,receipt
        def copied(capture,suite):
            for source,name in [(self.base.cuda,'generated.cu'),(self.base.metal,'generated.metal'),(self.base.cuda.with_suffix('.ptx'),'compiled.ptx')]:
                (capture/name).write_bytes(source.read_bytes())
        with self.base.context(compile_ptx),patch.object(cli,'copy_generated',copied):cli.compile_child(self.base.m,self.producer,'cuda')
        cli.write(self.producer/'run.json',dict(package_id=self.base.m['package_id'],backend='cuda',mode='compile-only',artifact_kind='ptx',ptxas_level=None,memory_limit_mb=2048))
        self.job_proof(self.producer)
        cli.collect(self.producer,self.producer/'artifacts.json')

    def job_proof(self,capture):
        stamp=time.time_ns();cli.write(capture/'execution.json',dict(passed=True,timeout_seconds=60,observation_error=None,cleanup_error=None,wait_completed_unix_ns=stamp))
        pre=dict(child_pid=os.getpid(),child_ppid=17,job_members=[os.getpid()],child_creation_filetime_ticks='100',observed_unix_ns=1,job_memory_limit_bytes=2048*1024*1024)
        cli.write(capture/'job.json',dict(records=[dict(child_pid=os.getpid(),wrapper_pid=17,pre_gate_verified=True,inspection_error=None,pre_gate=pre,post_wait=dict(pre,job_members=[],observed_unix_ns=stamp))]))
        before=dict(processes=[],service_status='unverified',observed_unix_ns=1);after=dict(before,observed_unix_ns=stamp+1)
        cli.write(capture/'observation.json',dict(before=before,after=after,comparison=compare_snapshots(before,after)))

    def popen(self,argv,**kwargs):
        self.assertEqual(argv[1:5],assembler.OPTIONS);self.assertFalse(kwargs['shell'])
        owner=self
        class Process:
            pid=os.getpid()+1000;done=False;terminated=False
            def wait(self,timeout):
                if owner.fail_wait and not self.terminated:raise subprocess.TimeoutExpired(argv,timeout)
                if not self.terminated:Path(argv[-1]).write_bytes(owner.payload)
                self.done=True;return owner.return_code
            def poll(self):return owner.return_code if self.done else None
            def terminate(self):self.terminated=True
        process=Process();self.processes.append(process);return process

    def inspect(self,process):
        return dict(child_pid=process.pid,child_ppid=os.getpid(),wrapper_pid=os.getpid(),job_members=[os.getpid(),process.pid],parent_observation='os_process_snapshot',child_creation_filetime_ticks='200',observed_unix_ns=time.time_ns())

    def context(self):
        stack=contextlib.ExitStack();stack.enter_context(patch.object(cli,'ROOT',self.package))
        stack.enter_context(patch.object(cli,'verify_package',side_effect=lambda root:self.base.m if Path(root)==self.source_package else self.m))
        stack.enter_context(patch.object(cli,'module',return_value=types.SimpleNamespace(normalized=cli.sha)))
        stack.enter_context(patch.object(assembler,'TOOL_SHA256',self.tool_sha))
        stack.enter_context(patch.object(assembler.subprocess,'Popen',self.popen))
        stack.enter_context(patch.object(assembler,'inspect_process',self.inspect))
        return stack

    def proof(self):
        with self.context():
            origin,_=cli.assembly_origin(self.m,self.source_package,self.producer)
            cli.write(self.capture/'assembly-request.json',dict(source_package=str(self.source_package),source_capture=str(self.producer),ptxas=str(self.tool),origin=origin))
            cli.assemble_child(self.m,self.capture,'cuda')
        cli.write(self.capture/'run.json',dict(mode='assemble-only',package_id=self.m['package_id'],backend='cuda',memory_limit_mb=2048))
        self.job_proof(self.capture)

    def audit(self):
        with self.context():return cli.audit_assemble_capture(self.m,self.capture,verify_artifacts=False)

    def test_real_upstream_auditor_and_process_gate_success_is_not_calculation(self):
        self.proof();r=self.audit();self.assertTrue(r['assembly_verified']);self.assertTrue(r['containment_verified'])
        self.assertFalse(r['calculation_verified']);self.assertFalse(r['preservation_verified']);self.assertFalse(r['passed'])
        self.assertEqual(self.base.native.calls.count('compile'),1);self.assertEqual(len(self.processes),1)
        self.assertEqual((self.capture/'compiled.cubin').read_bytes(),ELF)

    def test_wrong_tool_hash_stops_before_process(self):
        self.tool.write_bytes(b'MZwrong executable')
        with self.context(),self.assertRaisesRegex(ValueError,'pinned'):
            assembler.run(self.capture,self.tool,PTX,{},journal=producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertFalse(self.processes)

    def test_input_headers_are_not_rewritten_to_older_assembler(self):
        for raw in (PTX.replace(b'8.4',b'7.3'),PTX.replace(b'sm_86',b'sm_80'),b'not PTX'):
            with self.subTest(raw=raw),self.assertRaisesRegex(ValueError,'unchanged PTX'):assembler.validate_ptx(raw)
        self.assertFalse(self.processes)

    def test_upstream_failure_or_source_mismatch_stops_before_spawn(self):
        with self.context():
            wrong=copy.deepcopy(self.m);wrong['golden']['generated_normalized']['cuda']='wrong'
            with self.assertRaisesRegex(ValueError,'same sealed'):cli.assembly_origin(wrong,self.source_package,self.producer)
            facts=cli.load(self.producer/'execution.json');facts['passed']=False;cli.write(self.producer/'execution.json',facts);cli.collect(self.producer,self.producer/'artifacts.json')
            with self.assertRaisesRegex(ValueError,'producer not verified'):cli.assembly_origin(self.m,self.source_package,self.producer)
        self.assertFalse(self.processes)

    def test_bad_child_membership_terminates_only_owned_compiler(self):
        with self.context(),patch.object(assembler,'inspect_process',return_value=dict(child_pid=999)),self.assertRaisesRegex(RuntimeError,'validation Job'):
            origin,_=cli.assembly_origin(self.m,self.source_package,self.producer)
            cli.write(self.capture/'assembly-request.json',dict(source_package=str(self.source_package),source_capture=str(self.producer),ptxas=str(self.tool),origin=origin));cli.assemble_child(self.m,self.capture,'cuda')
        self.assertTrue(self.processes[0].terminated);self.assertFalse((self.capture/'assembly.json').exists())

    def test_timeout_preserves_partial_failure_and_does_not_retry(self):
        self.fail_wait=True
        with self.context(),self.assertRaises(subprocess.TimeoutExpired):
            origin,_=cli.assembly_origin(self.m,self.source_package,self.producer)
            assembler.run(self.capture,self.tool,PTX,origin,journal=producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertEqual(len(self.processes),1);self.assertTrue(self.processes[0].terminated)

    def test_failed_assembler_or_non_elf_cannot_publish_success(self):
        self.return_code=1
        with self.context(),self.assertRaisesRegex(RuntimeError,'exit code'):
            origin,_=cli.assembly_origin(self.m,self.source_package,self.producer)
            assembler.run(self.capture,self.tool,PTX,origin,journal=producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertTrue((self.capture/'compiled.cubin.partial').exists());self.assertFalse((self.capture/'compiled.cubin').exists())

    def test_zero_exit_with_non_elf_is_rejected_and_partial_is_preserved(self):
        self.payload=b'invalid binary'
        with self.context(),self.assertRaisesRegex(ValueError,'complete ELF'):
            origin,_=cli.assembly_origin(self.m,self.source_package,self.producer)
            assembler.run(self.capture,self.tool,PTX,origin,journal=producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertFalse((self.capture/'compiled.cubin').exists());self.assertTrue((self.capture/'compiled.cubin.partial').exists())

    def test_altered_native_argv_and_invented_calculation_are_not_proof(self):
        self.proof();path=self.capture/'phases.jsonl';saved=path.read_bytes();rows=[json.loads(line) for line in saved.decode().splitlines()]
        next(r for r in rows if r['stage']=='offline_ptxas' and r['state']=='entered')['argv'][2]='--opt-level=4'
        path.write_text('\n'.join(json.dumps(r) for r in rows)+'\n');self.assertFalse(self.audit()['assembly_verified']);path.write_bytes(saved)
        proof=cli.load(self.capture/'assembly.json');proof['calculation_verified']=True;cli.write(self.capture/'assembly.json',proof)
        self.assertFalse(self.audit()['assembly_verified'])

    def test_capture_claim_budget_and_child_mode_are_separate_and_environment_restored(self):
        fresh=self.root/'new-capture';env={'UNRELATED':'preserved'}
        with self.context(),patch.object(cli,'os',types.SimpleNamespace(**dict(vars(os),name='nt',environ=env))),patch.object(cli,'run_job') as job,patch.object(cli,'audit_assemble_capture',return_value=dict(mode='assemble-only',assembly_verified=True,calculation_verified=False)):
            result=cli.assemble_capture(fresh,60,self.root/'original',self.source_package,self.producer,self.tool)
            self.assertTrue(result['assembly_verified']);self.assertTrue(job.call_args.kwargs['assemble_only']);self.assertEqual(job.call_args.args[2],60)
            claim=(self.package/'assembly-claimed-cuda.json').read_bytes()
            with self.assertRaises(FileExistsError):cli.assemble_capture(self.root/'second',60,self.root/'original',self.source_package,self.producer,self.tool)
            self.assertEqual((self.package/'assembly-claimed-cuda.json').read_bytes(),claim)
            with self.assertRaises(ValueError):cli.assemble_capture(self.root/'large',61,self.root/'original',self.source_package,self.producer,self.tool)
        self.assertEqual(env,{'UNRELATED':'preserved'})

    def test_readonly_inspector_reuses_existing_observer_and_types_handles(self):
        import windows_validation_observer as observer
        dll=types.SimpleNamespace(CloseHandle=Mock());process=object()
        with patch.object(assembler.C,'WinDLL',return_value=dll,create=True) as loader,patch.object(observer,'inspect_job',return_value={'inspected':True}) as read:
            self.assertTrue(assembler.inspect_process(process)['inspected'])
        loader.assert_called_once_with('kernel32',use_last_error=True)
        self.assertIsNone(read.call_args.args[0].handle);self.assertIs(read.call_args.args[1],process)
        self.assertEqual(len(dll.CloseHandle.argtypes),1)

    def test_self_pid_cannot_be_accepted_as_a_second_compiler_process(self):
        snapshot=self.inspect(types.SimpleNamespace(pid=os.getpid()));self.assertFalse(assembler.contained(snapshot,os.getpid(),os.getpid()))

    def test_audit_rejects_tampered_elf_missing_event_or_job_cap(self):
        self.proof();path=self.capture/'compiled.cubin';raw=path.read_bytes();path.write_bytes(b'\x7fELF'+b'wrong'*20)
        self.assertFalse(self.audit()['assembly_verified']);path.write_bytes(raw)
        phase=self.capture/'phases.jsonl';saved=phase.read_bytes();phase.write_text('\n'.join(line for line in saved.decode().splitlines() if 'offline_ptxas_child' not in line)+'\n')
        self.assertFalse(self.audit()['assembly_verified']);phase.write_bytes(saved)
        job=cli.load(self.capture/'job.json');job['records'][0]['post_wait']['job_memory_limit_bytes']=None;cli.write(self.capture/'job.json',job)
        self.assertFalse(self.audit()['assembly_verified'])

    def test_forbidden_library_is_blocked_before_loading(self):
        def bad(*args,**kwargs):C.WinDLL('nvcuda.dll')
        with self.context(),patch.object(assembler,'run',side_effect=bad),patch.object(C,'WinDLL',create=True) as loader,self.assertRaisesRegex(RuntimeError,'forbidden'):
            origin,_=cli.assembly_origin(self.m,self.source_package,self.producer)
            cli.write(self.capture/'assembly-request.json',dict(source_package=str(self.source_package),source_capture=str(self.producer),ptxas=str(self.tool),origin=origin));cli.assemble_child(self.m,self.capture,'cuda')
        loader.assert_not_called()

if __name__=='__main__':unittest.main()
