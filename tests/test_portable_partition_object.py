"""Focus object origin, containment, failure and cache separation; no real exe/GPU."""
import base64,contextlib,copy,json,os,struct,subprocess,sys,time,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_partition_object as obj
import portable_offline_assembler as assembler
import test_portable_offline_assembly as baseline
from portable_ptx_partition import saved_partition
from test_portable_ptx_partition import PTX
cli=baseline.cli


def relocatable():
    raw=bytearray(192);raw[:7]=b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHI',raw,16,1,190,1);struct.pack_into('<Q',raw,40,64)
    struct.pack_into('<HHHHHH',raw,52,64,0,0,64,2,1)
    struct.pack_into('<IIQQQQIIQQ',raw,128,0,3,0,0,192,0,0,0,1,0)
    return bytes(raw)


class PartitionObjectTests(unittest.TestCase):
    def setUp(self):
        self.base=baseline.AssemblyTests()
        with patch.object(baseline,'PTX',PTX):self.base.setUp()
        self.addCleanup(self.base.doCleanups);self.base.payload=relocatable()
        self.base.source_package=self.base.source_package.resolve();self.base.package=self.base.package.resolve()
        self.root=self.base.root;self.capture=self.base.capture
        receipt=cli.load(self.base.producer/'compiler.json')['compile_artifact']
        self.cache=self.root/(receipt['key']+'.json');self.phases=self.base.producer/'phases.jsonl'
        self.cache.write_text(json.dumps(dict(identity=receipt['identity'],artifact_bytes=len(PTX),artifact_sha256=assembler.digest(PTX),artifact_base64=base64.b64encode(PTX).decode())))
        self.candidate=self.root/'candidate';saved_partition(self.cache,self.phases,self.candidate,'focus')
        self.request=dict(source_package=str(self.base.source_package),source_capture=str(self.base.producer),cache_entry=str(self.cache),phases=str(self.phases),candidate=str(self.candidate),ptxas=str(self.base.tool))

    def proof(self):
        with self.base.context():
            origin,_=cli.partition_object_origin(self.base.m,self.request)
            cli.write(self.capture/'object-request.json',dict(self.request,origin=origin));cli.partition_object_child(self.base.m,self.capture,'cuda')
        cli.write(self.capture/'run.json',dict(mode='partition-object-only',package_id=self.base.m['package_id'],backend='cuda',memory_limit_mb=2048));self.base.job_proof(self.capture)

    def audit(self):
        with self.base.context():return cli.audit_partition_object_capture(self.base.m,self.capture,verify_artifacts=False)

    def test_origin_chain_and_relocatable_object_do_not_certify_link_or_battle(self):
        self.proof();r=self.audit();self.assertTrue(r['object_verified'],r);self.assertTrue(r['containment_verified'])
        for name in ('passed','preservation_verified','link_verified','calculation_verified','partition_legal_verified'):self.assertFalse(r[name])
        self.assertEqual((self.capture/'focus.o').read_bytes(),relocatable());self.assertFalse((self.capture/'compiled.cubin').exists());self.assertEqual(len(self.base.processes),1)
        receipt=cli.load(self.capture/'object.json')['receipt'];self.assertEqual(receipt['identity']['artifact'],'diagnostic-relocatable-object');self.assertEqual(receipt['identity']['options'][-1],'--compile-only')

    def test_edited_candidate_rehashed_plan_or_wrong_upstream_cannot_spawn(self):
        self.candidate.joinpath('focus.ptx').write_bytes(b'changed')
        with self.base.context(),self.assertRaises(ValueError):cli.partition_object_origin(self.base.m,self.request)
        self.assertFalse(self.base.processes)
        producer=dict(ptx=dict(sha256='0'*64),cache_key='other')
        good=self.root/'good-candidate';saved_partition(self.cache,self.phases,good,'focus')
        with self.assertRaisesRegex(ValueError,'audited PTX producer'):obj.origin(self.cache,self.phases,good,producer)

    def test_elf_executable_wrong_machine_or_truncated_section_is_not_object(self):
        raw=relocatable()
        for at,data in ((16,struct.pack('<H',2)),(18,struct.pack('<H',62)),(40,struct.pack('<Q',1000)),(160,struct.pack('<Q',1))):
            changed=bytearray(raw);changed[at:at+len(data)]=data
            with self.subTest(at=at),self.assertRaises(ValueError):obj.validate_object(changed)
        with self.assertRaises(ValueError):obj.validate_object(raw[:100])

    def test_timeout_retains_failure_and_terminates_only_owned_child_without_retry(self):
        self.base.fail_wait=True
        with self.base.context(),self.assertRaises(subprocess.TimeoutExpired):
            origin,raw=cli.partition_object_origin(self.base.m,self.request)
            obj.run(self.capture,self.base.tool,raw,origin,journal=baseline.producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertEqual(len(self.base.processes),1);self.assertTrue(self.base.processes[0].terminated)
        self.assertIn('partition_object_failure',(self.capture/'phases.jsonl').read_text());self.assertFalse((self.capture/'focus.o').exists())

    def test_nonzero_exit_keeps_partial_and_forbids_object_publication(self):
        self.base.return_code=7
        with self.base.context(),self.assertRaisesRegex(RuntimeError,'exit code 7'):
            origin,raw=cli.partition_object_origin(self.base.m,self.request)
            obj.run(self.capture,self.base.tool,raw,origin,journal=baseline.producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertTrue((self.capture/'focus.o.partial').exists());self.assertFalse((self.capture/'focus.o').exists());self.assertEqual(len(self.base.processes),1)

    def test_bad_membership_is_rejected(self):
        with self.base.context(),patch.object(assembler,'inspect_process',return_value={}),self.assertRaisesRegex(RuntimeError,'validation Job'):
            origin,raw=cli.partition_object_origin(self.base.m,self.request)
            obj.run(self.capture,self.base.tool,raw,origin,journal=baseline.producer_test.Journal(self.capture/'phases.jsonl'))
        self.assertTrue(self.base.processes[0].terminated)

    def test_audit_rejects_command_tamper_missing_journal_cap_or_invented_link(self):
        self.proof();phase=self.capture/'phases.jsonl';saved=phase.read_bytes()
        for change in ('command','event'):
            rows=[json.loads(line) for line in saved.splitlines()]
            if change=='command':rows[4]['argv'].remove('--compile-only')
            else:rows.pop(5)
            phase.write_text('\n'.join(map(json.dumps,rows))+'\n');self.assertFalse(self.audit()['object_verified'])
        phase.write_bytes(saved);proof=cli.load(self.capture/'object.json');proof['link_verified']=True;cli.write(self.capture/'object.json',proof);self.assertFalse(self.audit()['object_verified']);proof['link_verified']=False;cli.write(self.capture/'object.json',proof)
        job=cli.load(self.capture/'job.json');job['records'][0]['post_wait']['job_memory_limit_bytes']=None;cli.write(self.capture/'job.json',job);self.assertFalse(self.audit()['object_verified'])

    def test_capture_claim_budget_and_environment_are_separate_from_assembly(self):
        env={'UNRELATED':'preserved'}
        with self.base.context(),patch.object(cli,'os',types.SimpleNamespace(**dict(vars(os),name='nt',environ=env))),patch.object(cli,'run_job') as job,patch.object(cli,'audit_partition_object_capture',return_value=dict(object_verified=True,calculation_verified=False)):
            args=(60,self.root/'original',self.base.source_package,self.base.producer,self.cache,self.phases,self.candidate,self.base.tool)
            cli.partition_object_capture(self.root/'new-object',*args)
            self.assertTrue(job.call_args.kwargs['partition_object_only']);self.assertEqual(job.call_args.args[2],60)
            self.assertTrue((self.base.package/'partition-object-claimed-cuda.json').exists());self.assertFalse((self.base.package/'assembly-claimed-cuda.json').exists())
            with self.assertRaises(FileExistsError):cli.partition_object_capture(self.root/'second',*args)
            with self.assertRaises(ValueError):cli.partition_object_capture(self.root/'large',61,*args[1:])
        self.assertEqual(env,{'UNRELATED':'preserved'})

    def test_child_dispatch_is_exclusive_and_passes_explicit_mode(self):
        cli.write(self.capture/'start.json',{})
        with self.base.context(),patch.object(cli,'partition_object_child') as dispatch:
            cli.child(self.capture,'cuda',partition_object_only=True);dispatch.assert_called_once()
            with self.assertRaises(ValueError):cli.child(self.capture,'cuda',compile_only=True,partition_object_only=True)
        with patch.object(cli,'child') as dispatch:cli.main(['_child','--capture',str(self.capture),'--backend','cuda','--partition-object-only'])
        self.assertTrue(dispatch.call_args.args[-1])

    def test_driver_library_is_blocked_before_loading(self):
        import ctypes as C
        def bad(*args,**kwargs):C.WinDLL('nvcuda.dll')
        with self.base.context():
            origin,_=cli.partition_object_origin(self.base.m,self.request);cli.write(self.capture/'object-request.json',dict(self.request,origin=origin))
            with patch.object(obj,'run',side_effect=bad),patch.object(C,'WinDLL',create=True) as loader,self.assertRaisesRegex(RuntimeError,'forbidden'):
                cli.partition_object_child(self.base.m,self.capture,'cuda')
            loader.assert_not_called()

    def test_cli_exit_distinguishes_object_failure_from_unknown_preservation(self):
        command=['partition-object','--capture',str(self.capture)]
        for flag in ('source-package','source-capture','cache-entry','phases','candidate','ptxas','original-workspace'):command.extend(['--'+flag,str(self.root)])
        for verified,preserved,code in ((False,True,1),(True,None,2),(True,False,2)):
            result=dict(mode='partition-object-only',object_verified=verified,preservation_verified=preserved)
            with patch.object(cli,'partition_object_capture',return_value=result),contextlib.redirect_stdout(__import__('io').StringIO()),self.assertRaises(SystemExit) as raised:cli.main(command)
            self.assertEqual(raised.exception.code,code)
