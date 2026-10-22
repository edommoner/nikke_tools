"""Shared source/claim/Job/journal admission for in-memory linking; no real DLL."""
import json,os,sys,time,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_jit_link as jit
import portable_jit_link_run as execution
import test_portable_device_linker as link_tests
from test_portable_jit_link import Library
cli=link_tests.cli


class JitLinkCaptureTests(unittest.TestCase):
    def setUp(self):
        self.link=link_tests.DeviceLinkerTests();self.link.setUp();self.addCleanup(self.link.doCleanups)
        self.f=self.link.f;self.tool=self.f.root/'nvJitLink_120_0.dll';self.tool.write_bytes(b'MZsynthetic JIT component')
        self.library=Library();self.capture=self.f.root/'jit-capture';self.capture.mkdir();self.driver=False
        self.request=dict(self.link.request,source_kind='jit-link',nvjitlink=str(self.tool));self.request.pop('nvlink')
        self.views=[];self.bad_cap=False;self.loader_calls=[]
    def view(self,capture):
        result=dict(child_pid=os.getpid(),child_ppid=17,wrapper_pid=os.getpid(),parent_observation='os_process_snapshot',child_creation_filetime_ticks='100',observed_unix_ns=time.time_ns(),job_members=[os.getpid()],job_memory_limit_bytes=1 if self.bad_cap else 2147483648)
        self.views.append(result);return result
    def loader(self,name,*args,**kwargs):
        self.loader_calls.append(str(name));self.assertEqual(Path(name).resolve(),self.tool.resolve());return self.library
    def context(self):
        stack=self.link.context();stack.enter_context(patch.object(jit,'TOOL_SHA256',jit.hashlib.sha256(self.tool.read_bytes()).hexdigest()))
        stack.enter_context(patch.object(execution,'inspect_context',self.view));stack.enter_context(patch.object(execution,'driver_loaded',lambda:self.driver))
        stack.enter_context(patch.object(execution.C,'WinDLL',self.loader,create=True));return stack
    def proof(self):
        self.f.base.job_proof(self.capture)
        with self.context():
            origin,_=cli.jit_link_origin(self.request);self.origin=origin
            cli.write(self.capture/'object-request.json',dict(self.request,origin=origin))
            cli.write(self.f.base.package/'jit-link-object-claimed-cuda.json',dict(package_id=self.f.base.m['package_id'],capture=str(self.capture.resolve()),origin=origin))
            cli.jit_link_child(self.f.base.m,self.capture,'cuda')
        cli.write(self.capture/'run.json',dict(mode='jit-link-object-only',package_id=self.f.base.m['package_id'],backend='cuda',memory_limit_mb=2048,status='finished'))
        self.f.base.job_proof(self.capture)
    def audit(self):
        with self.context():return cli.audit_jit_link_capture(self.f.base.m,self.capture,verify_artifacts=False)
    def test_shared_engine_source_and_api_journal_verify_link_but_never_battle(self):
        self.proof();r=self.audit();self.assertTrue(r['link_verified'],r);self.assertTrue(r['containment_verified']);self.assertFalse(r['calculation_verified']);self.assertFalse(r['passed'])
        self.assertEqual(len(self.loader_calls),1);self.assertEqual(self.library.calls.count('Complete'),1)
        self.assertEqual((self.capture/'module.relocatable.cubin').read_bytes(),(self.f.capture/'module.o').read_bytes())
        self.assertEqual((self.capture/'jit-linked.cubin').read_bytes(),link_tests.cubin())
        receipt=cli.load(self.capture/'jit-link.json')['receipt'];self.assertEqual(receipt['identity']['provider'],'diagnostic-nvjitlink')
        self.assertFalse(receipt['api_diagnostic']['source_origin_verified']);self.assertFalse(self.origin['current_battle_equivalence_verified'])
    def test_bad_origin_kind_or_recorded_input_hash_prevents_library_load(self):
        with self.context():
            with self.assertRaisesRegex(ValueError,'source kind'):cli.jit_link_origin(dict(self.request,source_kind='link'))
            with self.assertRaisesRegex(ValueError,'recorded SHA'):cli.jit_link_origin(dict(self.request,object_sha256='0'*64))
        self.assertEqual(self.loader_calls,[])
    def test_wrong_actual_job_cap_or_existing_driver_stops_before_loading_component(self):
        for which in ('cap','driver'):
            self.capture=self.f.root/('reject-'+which);self.capture.mkdir();self.bad_cap=which=='cap';self.driver=which=='driver'
            with self.subTest(which=which),self.assertRaises((ValueError,RuntimeError)):self.proof()
            self.assertFalse((self.capture/'jit-linked.cubin').exists());self.assertFalse((self.capture/'jit-link.json').exists())
        self.assertEqual(self.loader_calls,[])
    def test_api_failure_retains_diagnostic_and_destroys_without_publishing(self):
        self.library.fail='Complete';self.library.error_log=b'saved link error'
        with self.assertRaises(jit.JitLinkError):self.proof()
        rows=[json.loads(line) for line in (self.capture/'phases.jsonl').read_text().splitlines()]
        diagnostic=next(r['diagnostic'] for r in rows if r['stage']=='module_jit_link_failure')
        self.assertEqual(diagnostic['error_log'],'saved link error');self.assertEqual(self.library.calls.count('Destroy'),1)
        self.assertFalse((self.capture/'jit-linked.cubin').exists());self.assertTrue((self.capture/'module.relocatable.cubin').exists())
    def test_driver_after_link_cannot_publish(self):
        import portable_partition_object as obj
        from portable_phase_audit import Journal
        self.f.base.job_proof(self.capture)
        with self.context():
            origin,raw=cli.jit_link_origin(self.request)
            with patch.object(execution,'driver_loaded',side_effect=[False,False,True]),self.assertRaisesRegex(RuntimeError,'driver module'):
                obj.run(self.capture,self.tool,raw,origin,journal=Journal(self.capture/'phases.jsonl'))
        self.assertFalse((self.capture/'jit-linked.cubin').exists());self.assertEqual(self.library.calls.count('Destroy'),1)
    def test_dll_changed_during_api_cannot_publish(self):
        self.f.base.job_proof(self.capture)
        with self.context():
            origin,raw=cli.jit_link_origin(self.request)
            original=jit.link_cubin
            def changed(*args):
                result=original(*args);self.tool.write_bytes(b'MZchanged');return result
            with patch.object(jit,'link_cubin',changed),self.assertRaisesRegex(ValueError,'pinned NVIDIA'):
                from portable_phase_audit import Journal
                execution.run(self.capture,self.tool,raw,origin,journal=Journal(self.capture/'phases.jsonl'))
        self.assertFalse((self.capture/'jit-linked.cubin').exists());self.assertEqual(self.library.calls.count('Destroy'),1)

    def test_missing_api_return_wrong_scope_or_cap_tampering_rejects_saved_result(self):
        self.proof();phase=self.capture/'phases.jsonl';saved=phase.read_bytes()
        rows=[json.loads(line) for line in saved.splitlines()]
        remove=next(i for i,r in enumerate(rows) if r['stage']==jit.symbol('Complete') and r['state']=='returned');rows.pop(remove)
        phase.write_text('\n'.join(map(json.dumps,rows))+'\n');self.assertFalse(self.audit()['link_verified']);phase.write_bytes(saved)
        rows=[json.loads(line) for line in saved.splitlines()];next(r for r in rows if r['stage']=='module_jit_link_job')['inspection']['job_memory_limit_bytes']=None
        phase.write_text('\n'.join(map(json.dumps,rows))+'\n');self.assertFalse(self.audit()['link_verified']);phase.write_bytes(saved)
        proof=cli.load(self.capture/'jit-link.json');proof['calculation_verified']=True;cli.write(self.capture/'jit-link.json',proof)
        self.assertFalse(self.audit()['link_verified'])
    def test_jit_claim_and_run_job_flag_are_separate_and_budget_is_restored(self):
        with self.context():origin,_=cli.jit_link_origin(self.request)
        env={'UNRELATED':'same'};folder=self.f.root/'parent-jit'
        with self.context(),patch.object(cli,'os',types.SimpleNamespace(**dict(vars(os),name='nt',environ=env))),patch.object(cli,'run_job') as run,patch.object(cli,'audit_jit_link_capture',return_value=dict(object_verified=True,link_verified=True,calculation_verified=False)):
            cli.object_capture(folder,60,self.f.root/'original',dict(self.request))
            self.assertEqual(run.call_args.kwargs,dict(jit_link_object_only=True));self.assertTrue((self.f.base.package/'jit-link-object-claimed-cuda.json').exists())
            self.assertTrue((self.f.base.package/'module-object-claimed-cuda.json').exists());self.assertEqual(env,{'UNRELATED':'same'})
            with self.assertRaises(FileExistsError):cli.object_capture(self.f.root/'duplicate',60,self.f.root/'original',dict(self.request))
            self.assertEqual(run.call_count,1)
            with self.assertRaises(ValueError):cli.object_capture(self.f.root/'over-budget',61,self.f.root/'original',self.request)
    def test_child_mode_is_explicit_and_cannot_mix_with_smoke_or_native_link(self):
        capture=self.f.root/'mode';capture.mkdir();(capture/'start.json').write_text('{}')
        with patch.object(cli,'verify_package',return_value=self.f.base.m),patch.object(cli,'jit_link_child') as child:
            cli.child(capture,'cuda',jit_link_object_only=True);child.assert_called_once()
        for options in (dict(jit_link_object_only=True,smoke=True),dict(jit_link_object_only=True,link_object_only=True)):
            with self.subTest(options=options),self.assertRaises(ValueError):cli.child(capture,'cuda',**options)


if __name__=='__main__':unittest.main()
