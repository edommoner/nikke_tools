"""Static CUDA executable and bounded saved-object linking; synthetic tools only."""
import contextlib,copy,json,os,struct,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_device_linker as linker
import portable_partition_object as obj
import test_portable_module_object as module_tests
cli=module_tests.cli


def cubin(entry=b'portableEvents',parameter_bytes=48):
    strings=b'\0'+entry+b'\0SLANG_globalParams\0';names=b'\0.text\0.nv.constant3\0.strtab\0.symtab\0.shstrtab\0'
    symbols=b'\0'*24+struct.pack('<IBBHQQ',1,0x12,0x10,1,0,16)+struct.pack('<IBBHQQ',strings.index(b'SLANG_globalParams'),0x11,0,2,0,parameter_bytes)
    raw=bytearray(120);raw[:7]=b'\x7fELF\x02\x01\x01';rows=[(0,0,0,0,0,0,0,0,0,0)]
    for name,typ,flags,data,link,entsize in ((b'.text',1,6,b'\0'*16,0,0),(b'.nv.constant3',1,2,b'\0'*48,0,0),(b'.strtab',3,0,strings,0,0),(b'.symtab',2,0,symbols,3,24),(b'.shstrtab',3,0,names,0,0)):
        raw.extend(b'\0'*((-len(raw))%8));offset=len(raw);raw.extend(data);rows.append((names.index(name),typ,flags,0,offset,len(data),link,0,8,entsize))
    raw.extend(b'\0'*((-len(raw))%8));shoff=len(raw)
    for row in rows:raw.extend(struct.pack('<IIQQQQIIQQ',*row))
    struct.pack_into('<HHI',raw,16,2,190,124);struct.pack_into('<QQI',raw,32,64,shoff,0x560556);struct.pack_into('<HHHHHH',raw,52,64,56,1,64,6,5)
    struct.pack_into('<IIQQQQQQ',raw,64,1,5,rows[1][4],0,0,16,16,8)
    return bytes(raw)


class DeviceLinkerTests(unittest.TestCase):
    def setUp(self):
        self.module=module_tests.ModuleObjectTests();self.module.setUp();self.addCleanup(self.module.doCleanups)
        self.f=self.module.f;source,_=self.module.proof();f=self.f
        cli.write(f.base.package/'module-object-claimed-cuda.json',dict(package_id=f.base.m['package_id'],capture=str(f.capture.resolve()),origin=source));cli.collect(f.capture,f.capture/'artifacts.json')
        self.tool=f.root/'nvlink.exe';self.tool.write_bytes(b'MZsynthetic linker')
        self.capture=f.root/'link';self.capture.mkdir();self.processes=[];self.timeout=False;self.code=0;self.payload=cubin()
        self.request=dict(source_kind='link',object_package=str(f.base.package),object_capture=str(f.capture),object_sha256=linker.digest((f.capture/'module.o').read_bytes()),nvlink=str(self.tool))

    def popen(self,argv,**kwargs):
        self.assertEqual(argv[1:4],linker.OPTIONS);self.assertFalse(kwargs['shell']);owner=self
        self.assertEqual(Path(argv[-3]).name,'module.relocatable.cubin');self.assertEqual(Path(argv[-3]).suffix,'.cubin')
        self.assertEqual(Path(argv[-1]).name,'linked.partial.cubin');self.assertEqual(Path(argv[-1]).suffix,'.cubin')
        class Process:
            pid=os.getpid()+2000;done=False;terminated=False
            def wait(self,timeout):
                if not self.terminated:Path(argv[-1]).write_bytes(owner.payload)
                if owner.timeout and not self.terminated:raise subprocess.TimeoutExpired(argv,timeout)
                self.done=True;return owner.code
            def poll(self):return owner.code if self.done else None
            def terminate(self):self.terminated=True
            def release(self):
                return dict(protocol='create-suspended-v1',created_suspended=True,creation_flags=0x4004,primary_thread_id=self.pid+1,resume_previous_count=1)
            def close(self):self.closed=True
        process=Process();self.processes.append(process);return process

    def context(self):
        stack=self.f.context();stack.enter_context(patch.object(linker,'TOOL_SHA256',linker.digest(self.tool.read_bytes())))
        stack.enter_context(patch.object(obj.subprocess,'Popen',self.popen));stack.enter_context(patch.object(obj,'SuspendedNativeProcess',self.popen));return stack

    def proof(self):
        with self.context():
            origin,_=cli.partition_object_origin(self.f.base.m,self.request,link_object=True);cli.write(self.capture/'object-request.json',dict(self.request,origin=origin))
            cli.partition_object_child(self.f.base.m,self.capture,'cuda',link_object=True)
        cli.write(self.capture/'run.json',dict(mode='link-object-only',package_id=self.f.base.m['package_id'],backend='cuda',memory_limit_mb=2048,status='finished'));self.f.base.job_proof(self.capture)

    def audit(self):
        with self.context():return cli.audit_partition_object_capture(self.f.base.m,self.capture,verify_artifacts=False,link_object=True)

    def test_static_executable_requires_target_real_entry_parameters_and_payload_ranges(self):
        result=linker.validate_cubin(cubin());self.assertEqual(result['cuda_format_version'],124);self.assertEqual(result['static_bindings']['SLANG_globalParams']['bytes'],48)
        variants=[cubin(entry=b'missingKernel'),cubin(parameter_bytes=40),cubin()[:150]]
        for offset,data in ((16,struct.pack('<H',1)),(18,struct.pack('<H',62)),(20,struct.pack('<I',0)),(48,struct.pack('<I',0x560550)),(32,struct.pack('<Q',999999))):
            raw=bytearray(cubin());raw[offset:offset+len(data)]=data;variants.append(raw)
        for raw in variants:
            with self.subTest(raw=raw[:24]),self.assertRaises(ValueError):linker.validate_cubin(raw)

    def test_same_native_engine_links_saved_object_and_never_certifies_calculation(self):
        self.proof();r=self.audit();self.assertTrue(r['object_verified'],r);self.assertTrue(r['link_verified']);self.assertTrue(r['containment_verified']);self.assertFalse(r['preservation_verified']);self.assertFalse(r['calculation_verified']);self.assertFalse(r['passed'])
        self.assertEqual((self.capture/'module.relocatable.cubin').read_bytes(),(self.f.capture/'module.o').read_bytes());self.assertEqual((self.capture/'linked.cubin').read_bytes(),cubin());self.assertEqual(len(self.processes),1);self.assertEqual(len(self.f.base.processes),1)
        proof=cli.load(self.capture/'link.json');self.assertEqual(proof['receipt']['identity']['provider'],'diagnostic-nvlink');self.assertEqual(proof['receipt']['identity']['artifact'],'diagnostic-linked-cubin');self.assertEqual(proof['receipt']['identity']['input_container'],'raw-device-elf-cubin-v1');self.assertFalse(proof['origin']['current_battle_equivalence_verified'])

    def test_link_audit_requires_suspended_creation_and_a_single_resume(self):
        self.proof();phase=self.capture/'phases.jsonl';saved=phase.read_bytes()
        for field,value in (('created_suspended',False),('creation_flags',0x4000),('resume_previous_count',0),('primary_thread_id',0)):
            rows=[json.loads(line) for line in saved.splitlines()];rows[5]['native_launch'][field]=value
            phase.write_text('\n'.join(map(json.dumps,rows))+'\n')
            with self.subTest(field=field):self.assertFalse(self.audit()['link_verified'])
        phase.write_bytes(saved)

    def test_original_object_hash_or_claim_mismatch_and_mode_mix_stop_before_linker(self):
        with self.context():
            with self.assertRaisesRegex(ValueError,'source kind'):cli.partition_object_origin(self.f.base.m,self.request)
            bad=dict(self.request,object_sha256='0'*64)
            with self.assertRaisesRegex(ValueError,'recorded SHA'):cli.linked_object_origin(bad)
            (self.f.base.package/'module-object-claimed-cuda.json').unlink()
            with self.assertRaises(FileNotFoundError):cli.linked_object_origin(self.request)
        self.assertFalse(self.processes)

    def test_failed_native_observation_is_retained_without_certifying_an_early_exit(self):
        with self.context():
            origin,raw=cli.linked_object_origin(self.request)
            snapshot=dict(wrapper_pid=os.getpid(),child_pid=os.getpid()+2000,job_members=[os.getpid()],parent_observation='os_process_snapshot')
            def exited(argv,**kwargs):
                process=self.popen(argv,**kwargs);process.done=True;self.code=7;return process
            with self.assertRaisesRegex(RuntimeError,'not in the validation Job'):
                obj.run(self.capture,self.tool,raw,origin,journal=module_tests.focus_tests.baseline.producer_test.Journal(self.capture/'phases.jsonl'),popen=exited,inspector=lambda process:snapshot)
        rows=[json.loads(line) for line in (self.capture/'phases.jsonl').read_text().splitlines()]
        rejected=[r for r in rows if r['stage']=='module_link_child' and r['state']=='rejected']
        self.assertEqual(len(rejected),1);self.assertEqual(rejected[0]['inspection'],snapshot)
        self.assertEqual(rejected[0]['observed_return_code'],7);self.assertEqual(len(self.processes),1)
        self.assertFalse(self.processes[0].terminated);self.assertFalse((self.capture/'linked.cubin').exists())
        self.assertFalse(any(r['stage']=='module_link_receipt' for r in rows))

    def test_linker_timeout_keeps_partial_and_terminates_owned_process_without_retry(self):
        self.timeout=True
        with self.context(),self.assertRaises(subprocess.TimeoutExpired):
            origin,raw=cli.linked_object_origin(self.request);obj.run(self.capture,self.tool,raw,origin,journal=module_tests.focus_tests.baseline.producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertEqual(len(self.processes),1);self.assertTrue(self.processes[0].terminated);self.assertTrue((self.capture/'linked.partial.cubin').exists());self.assertFalse((self.capture/'linked.cubin').exists())

    def test_audit_rejects_removed_host_preservation_flag_or_modified_output(self):
        self.proof();phase=self.capture/'phases.jsonl';saved=phase.read_bytes();rows=[json.loads(x) for x in saved.splitlines()];rows[4]['argv'].remove('--ignore-host-info');phase.write_text('\n'.join(map(json.dumps,rows))+'\n');self.assertFalse(self.audit()['link_verified']);phase.write_bytes(saved)
        (self.capture/'linked.cubin').write_bytes(cubin()+b'changed');self.assertFalse(self.audit()['link_verified'])
        with self.context(),self.assertRaisesRegex(ValueError,'Wrong diagnostic'):cli.audit_partition_object_capture(self.f.base.m,self.capture,verify_artifacts=False,module_object=True)

    def test_link_claim_job_flag_budget_and_parent_environment_are_isolated(self):
        f=self.f;env={'UNRELATED':'preserved'}
        with self.context():self._origin=cli.linked_object_origin(self.request)
        with self.context(),patch.object(cli,'os',types.SimpleNamespace(**dict(vars(os),name='nt',environ=env))),patch.object(cli,'run_job') as job,patch.object(cli,'audit_partition_object_capture',return_value=dict(object_verified=True,link_verified=True,calculation_verified=False)):
            # Origin must use the real upstream auditor while only the final
            # new-capture audit is stubbed for this controller test.
            with patch.object(cli,'linked_object_origin',return_value=self._origin):
                args=(60,f.root/'original',f.base.package,f.capture,self.request['object_sha256'],self.tool)
                cli.link_object_capture(f.root/'link-run',*args)
                self.assertEqual(job.call_args.kwargs,dict(link_object_only=True));self.assertTrue((f.base.package/'link-object-claimed-cuda.json').exists());self.assertTrue((f.base.package/'module-object-claimed-cuda.json').exists())
                with self.assertRaises(FileExistsError):cli.link_object_capture(f.root/'second',*args)
                with self.assertRaises(ValueError):cli.link_object_capture(f.root/'large',61,*args[1:])
        self.assertEqual(env,{'UNRELATED':'preserved'})

    def test_link_child_flag_is_explicit_and_exclusive(self):
        cli.write(self.capture/'start.json',{})
        with self.context(),patch.object(cli,'partition_object_child') as dispatch:
            cli.child(self.capture,'cuda',link_object_only=True);self.assertTrue(dispatch.call_args.kwargs['link_object'])
            with self.assertRaises(ValueError):cli.child(self.capture,'cuda',module_object_only=True,link_object_only=True)
        with patch.object(cli,'child') as dispatch:cli.main(['_child','--capture',str(self.capture),'--backend','cuda','--link-object-only'])
        self.assertTrue(dispatch.call_args.args[8]);self.assertFalse(dispatch.call_args.args[7])

    def test_wrong_linker_digest_stops_before_process(self):
        expected=linker.digest(self.tool.read_bytes())
        with self.context(),patch.object(linker,'TOOL_SHA256',expected):
            origin,raw=cli.linked_object_origin(self.request);self.tool.write_bytes(b'MZdifferent compiler')
            with self.assertRaisesRegex(ValueError,'pinned NVIDIA'):obj.run(self.capture,self.tool,raw,origin,journal=module_tests.focus_tests.baseline.producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertFalse(self.processes)

    def test_driver_load_is_forbidden_in_link_only_child(self):
        import ctypes as C
        def bad(*args,**kwargs):C.WinDLL('nvcuda.dll')
        with self.context():
            origin,_=cli.linked_object_origin(self.request);cli.write(self.capture/'object-request.json',dict(self.request,origin=origin))
            with patch.object(obj,'run',side_effect=bad),patch.object(C,'WinDLL',create=True) as loader,self.assertRaisesRegex(RuntimeError,'forbidden'):
                cli.partition_object_child(self.f.base.m,self.capture,'cuda',link_object=True)
            loader.assert_not_called()
        self.assertFalse(self.processes)
