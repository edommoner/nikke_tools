"""Controller migration preserves transport bodies and cannot replay an origin."""
import ast,copy,importlib.util,json,os,sys,types,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_gpu_recovery as recovery
import portable_gpu_recovery_package as capsule
import test_portable_staged_preflight as fixture
cli=fixture.cli
s=importlib.util.spec_from_file_location('recovery_packet',ROOT/'scripts/run-gpu-packet.py');packet=importlib.util.module_from_spec(s);s.loader.exec_module(packet)


def bridged_flow():
    source=(ROOT/'app/portable_staged_preflight.py').read_text()
    if 'from portable_gpu_recovery import admit_context' not in source:source=capsule.patch_flow(source)
    module=types.ModuleType('recovery_test_flow');exec(compile(source,'<reviewed-recovery-flow>','exec'),module.__dict__)
    return module


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.StagedPreflightTests();self.f.setUp();self.addCleanup(self.f.doCleanups);f=self.f
        self.flow=bridged_flow();p=patch.dict(sys.modules,{'portable_staged_preflight':self.flow});p.start();self.addCleanup(p.stop)
        # Keep logical transport fixtures independent of the actual OS, as the
        # original staged fixture does. OriginTerminalTests below still use
        # the real Job receipt checker on every platform, without a skip.
        p=patch.object(self.flow,'os',SimpleNamespace(name='posix',fsync=os.fsync,getpid=os.getpid));p.start();self.addCleanup(p.stop)
        p=patch.object(self.flow,'host',return_value=dict(platform='fixture',python_sha256='pinned'));p.start();self.addCleanup(p.stop)
        self.pkg=f.root/'new-owner';self.pkg.mkdir();self.tx=f.root/'recovery-proof';self.gpu=f.root/'new-gpu'
        self.m=copy.deepcopy(f.m);self.m.update(package_id='new-owner',controller_gpu_recovery=dict(base_package_id='owned'))
        cli.write(self.pkg/'gpu-package.json',self.m)
        oldtx=f.tx;oldtx.mkdir();(oldtx/'input.bin').write_bytes(f.data)
        cli.write(oldtx/'transaction.json',dict(native_indices=[0,2]))
        cli.write(oldtx/'gpu-execution-claimed.json',dict(package_id='owned',nonce='old-consumed'))
        failed=f.root/'old-failed';(failed/'proof').mkdir(parents=True)
        cli.write(failed/'proof/staged-preflight.json',dict(transaction=str(oldtx)))
        parent=dict(transaction=str(oldtx),input=cli.transport_input_receipt(f.m,f.data,1),input_count=3,native_cases=2,
            groups=2,fresh_child_pids=[100,200],stage_envelopes=[],group_anchors=[])
        self.request={k:str(f.root/k) for k in recovery.FIELDS}
        self.request.update(source_package=str(f.pkg),source_capture=str(failed),gpu_capture=str(self.gpu))
        compiler=Path(self.request['slang_root']);(compiler/'bin').mkdir(parents=True);(compiler/'bin'/('slangc.exe' if os.name=='nt' else 'slangc')).write_bytes(b'not executed')
        Path(self.request['generation_cache']).mkdir()
        linked=dict(package=self.request['linked_package'],capture=self.request['linked_capture'])
        cli.write(failed/'proof/linked-artifact-request.json',linked)
        self.linked=dict(receipt=dict(key='linked'),artifact='saved.cubin')
        self.c=SimpleNamespace(**{**vars(f.c),'ROOT':self.pkg,'module':lambda _:packet,'verify_package':lambda _:self.m,
            'required_generation_snapshot':lambda m:({},dict(generation=dict(key='paired-key'))),
            'saved_linked_admission':lambda m,r:self.linked})
        self.c.native_value=lambda *a:(_ for _ in ()).throw(AssertionError('No native oracle'))
        self.c.cpu_test_groups=lambda *a:(_ for _ in ()).throw(AssertionError('No repeated old tests'))
        self.origin=(f.m,parent,dict(inventory_sha256='origin-fingerprint'),[f.pkg,oldtx,failed])
        p=patch.object(recovery,'origin_evidence',return_value=self.origin);p.start();self.addCleanup(p.stop)
        p=patch.dict(os.environ,dict(NIKKE_SLANG_ROOT=self.request['slang_root'],NIKKE_SLANG_GENERATION_CACHE=self.request['generation_cache'],NIKKE_SLANG_GENERATION_REQUIRED='1'));p.start();self.addCleanup(p.stop)

    def begin(self):return recovery.begin(self.c,self.tx,self.request)

    def test_new_owner_preserves_old_claims_and_uses_existing_transport_boundaries(self):
        old=(self.f.tx/'gpu-execution-claimed.json').read_bytes();result=self.begin()
        self.assertTrue(result['transaction_ready']);self.assertEqual(result['native_oracles_run'],0)
        self.assertFalse(result['native_values_reused']);self.assertFalse(result['original_failure_promoted'])
        self.assertEqual((self.f.tx/'gpu-execution-claimed.json').read_bytes(),old)
        self.assertEqual(cli.load(self.tx/'transaction.json')['case_groups'],[])
        self.gpu.mkdir();cli.write(self.gpu/'run.json',dict(package_id='new-owner',mode='staged-gpu',backend='cuda',input_protocol='staged-prepared-v1'))
        cli.write(self.gpu/'linked-artifact-request.json',dict(package=self.request['linked_package'],capture=self.request['linked_capture']))
        receipt=self.flow.prepare_gpu_input(self.c,self.m,self.tx,self.gpu,'cuda')
        self.assertTrue(receipt['all_native_preflight_verified']);self.assertFalse(receipt['calculation_verified'])
        self.flow.claim_execution(self.c,self.tx,self.gpu)
        self.assertEqual(self.flow.read_gpu_input(self.c,self.m,self.gpu),(self.f.data,1))
        with self.assertRaises(FileExistsError):self.flow.claim_execution(self.c,self.tx,self.gpu)
        self.assertEqual((self.f.tx/'gpu-execution-claimed.json').read_bytes(),old)

    def test_stable_origin_ledger_rejects_another_owner_even_after_failure(self):
        self.begin();other=self.f.root/'another-owner';other.mkdir();m=dict(self.m,package_id='another-owner')
        cli.write(other/'gpu-package.json',m);c=SimpleNamespace(**{**vars(self.c),'ROOT':other,'verify_package':lambda _:m})
        req=dict(self.request,gpu_capture=str(self.f.root/'another-gpu'))
        with self.assertRaises(FileExistsError):recovery.begin(c,self.f.root/'another-proof',req)
        self.assertFalse((self.f.root/'another-proof').exists())

    def test_missing_environment_or_cache_does_not_consume_the_origin_ledger(self):
        ledger=recovery.ledger_path(self.c,self.request,'owned')
        with patch.dict(os.environ,NIKKE_SLANG_GENERATION_REQUIRED='0'),self.assertRaises(ValueError):self.begin()
        self.assertFalse(ledger.exists());self.assertFalse(self.tx.exists())
        def missing(m):raise RuntimeError('Required generation cache miss')
        with patch.object(self.c,'required_generation_snapshot',side_effect=missing),self.assertRaises(RuntimeError):self.begin()
        self.assertFalse(ledger.exists());self.assertFalse((self.pkg/'gpu-claimed-cuda.json').exists())
        self.assertTrue((self.tx/'failure.json').is_file())

    def test_ledger_input_linked_request_and_generation_environment_cannot_drift(self):
        self.begin();m,c=self.flow.context(self.c,self.tx,'cuda',self.gpu)
        ledger=Path(c['recovery_parent']['ledger']);raw=ledger.read_bytes();ledger.write_bytes(raw+b' ')
        # Whitespace alone retains JSON identity; an actual ownership change does not.
        changed=cli.load(ledger);changed['nonce']='different';cli.write(ledger,changed)
        with self.assertRaises(ValueError):recovery.admit_context(self.c,m,c)
        ledger.write_bytes(raw)
        with patch.dict(os.environ,NIKKE_SLANG_GENERATION_CACHE=str(self.f.root/'wrong')),self.assertRaises(ValueError):recovery.admit_context(self.c,m,c)
        self.gpu.mkdir();cli.write(self.gpu/'run.json',dict(package_id='new-owner',mode='staged-gpu',backend='cuda',input_protocol='staged-prepared-v1'))
        cli.write(self.gpu/'linked-artifact-request.json',dict(package='substitute',capture='substitute'))
        with self.assertRaises(ValueError):recovery.admit_context(self.c,m,c)

    def test_original_normal_preflight_and_unprepared_child_are_rejected(self):
        for name in ('run','preflight-begin','preflight-plan','preflight-resume','preflight-native-group'):
            with self.subTest(name=name),self.assertRaises(ValueError):recovery.dispatch(self.c,lambda _:self.fail('Must not forward'),[name])
        self.gpu.mkdir();cli.write(self.gpu/'run.json',dict(mode='gpu'))
        with self.assertRaises(ValueError):recovery.dispatch(self.c,lambda _:self.fail('Must not forward'),['_child','--capture',str(self.gpu)])

    def test_wrapper_derives_frozen_generation_pair_in_ordinary_recipe_reconstruction(self):
        plan=packet.recipe('new-owner','preflight-recover','cuda',self.f.root/'stage',self.f.root/'workspace',180,self.request)
        self.assertEqual(plan['generation_settings'],recovery.settings(self.request))
        self.assertEqual(packet.proof_arguments(plan)[0],'preflight-recover')
        self.assertEqual(packet.recipe('new-owner','preflight-recover','cuda',self.f.root/'stage',self.f.root/'workspace',180,self.request),plan)
        with self.assertRaises(ValueError):packet.recipe('new-owner','preflight-recover','cuda',self.f.root/'stage',self.f.root/'workspace',180,self.request,generation_settings=dict(slang_root='/other',generation_cache='/other'))
        proof=self.begin();self.assertTrue(packet.verified_staged(proof,'preflight-recover','new-owner'))
        self.assertFalse(packet.verified_staged(dict(proof,original_failure_promoted=True),'preflight-recover','new-owner'))


class RecoverySourceTests(unittest.TestCase):
    def test_surgical_cli_and_flow_patch_preserves_original_calculation_and_claim_bodies(self):
        old_cli='from types import SimpleNamespace\ndef child():\n return 42\ndef main(argv=None):\n return argv\nif __name__ == "__main__":\n main()\n'
        # The fixture may itself be the migrated capsule; recover the original
        # source tree by undoing only the two reviewed bridge insertions.
        source=(ROOT/'app/portable_staged_preflight.py').read_text();tree=ast.parse(source)
        context=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='context')
        context.body=[n for n in context.body if not (isinstance(n,ast.If) and ast.unparse(n.test)=="m.get('controller_gpu_recovery') and 'recovery_parent' not in c")]
        for i,n in enumerate(context.body):
            if isinstance(n,ast.If) and ast.unparse(n.test)=="'recovery_parent' in c":context.body[i]=n.orelse[0]
        admit=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admit')
        admit.body=[n for n in admit.body if not (isinstance(n,ast.If) and ast.unparse(n.test)=="'recovery_parent' in c")]
        old_flow=ast.unparse(tree)
        old={'scripts/nikke_gpu.py':old_cli,'app/portable_staged_preflight.py':old_flow,'scripts/run-gpu-packet.py':''}
        new=dict(old,**{'scripts/nikke_gpu.py':capsule.patch_cli(old_cli),'app/portable_staged_preflight.py':capsule.patch_flow(old_flow)})
        capsule.guarded_sources(old,new)
        for path,needle in (('scripts/nikke_gpu.py','return 42'),('app/portable_staged_preflight.py',"exclusive(transaction / 'gpu-execution-claimed.json'")):
            changed=dict(new);changed[path]=changed[path].replace(needle,needle.replace('42','43') if '42' in needle else "exclusive(transaction / 'another-claim.json'",1)
            with self.subTest(path=path),self.assertRaises(ValueError):capsule.guarded_sources(old,changed)


class OriginTerminalTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from windows_validation_observer import compare_snapshots
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);base=Path(tmp.name).resolve()
        self.outer=base/'audit';self.outer.mkdir();(self.outer/'proof').mkdir()
        self.manifest=dict(package_id='auditor');self.request=dict(source_package=str(base/'old'),source_capture=str(base/'failed'),base_package_id='a'*64)
        request=dict(source_package=self.request['source_package'],source_capture=self.request['source_capture'],expected_package_id='a'*64)
        plan=packet.recipe('auditor',packet.ORIGIN_STAGE,'cuda',self.outer,base/'workspace',180,request)
        cli.write(self.outer/'recipe.json',plan)
        self.proof=dict(schema='staged-origin-check-v1',mode='saved-staged-origin-audit',package_id='a'*64,
            passed=True,native_admission_revalidated=True,host_revalidated=True,process_preservation_verified=True,
            execution_permitted=False,recovery_admission_verified=False,linked_artifact_revalidated=False,calculation_verified=False,
            claims_modified=False,native_values_reused=False,gpu_calls=0,compiler_calls=0,native_calls=0)
        cli.write(self.outer/'proof/result.json',self.proof)
        cli.write(self.outer/'stage-result.json',dict(package_id='auditor',stage=packet.ORIGIN_STAGE,stage_verified=True,proof_result=self.proof,calculation_verified=False))
        cli.write(self.outer/'execution.json',dict(passed=True,timed_out=False,child_exit_code=0,final_child_exit_code=0,below_normal_priority=True,timeout_seconds=179,error=None,cleanup_error=None,observation_error=None))
        state=dict(child_pid=20,child_ppid=10,child_creation_filetime_ticks=1,job_members=[20],job_memory_limit_bytes=2147483648,observed_unix_ns=0)
        cli.write(self.outer/'job.json',dict(records=[dict(child_pid=20,wrapper_pid=10,pre_gate_verified=True,inspection_error=None,pre_gate=state,post_wait=dict(state,job_members=[],observed_unix_ns=100))]))
        (self.outer/'preparation.jsonl').write_text(json.dumps(dict(pid=20,wall_time_ns=1,monotonic_ns=1))+'\n')
        snapshot=dict(processes=[],service_status='unverified');cli.write(self.outer/'observation.json',dict(before=snapshot,after=snapshot,comparison=compare_snapshots(snapshot,snapshot)))
        self.c=SimpleNamespace(**{**vars(cli),'module':lambda _:packet})

    def test_real_job_timeline_validates_cpu_origin_without_service_promotion(self):
        self.assertEqual(recovery.origin_terminal(self.c,self.outer,self.manifest,self.request),self.proof)

    def test_false_terminals_and_forged_owner_fail_closed(self):
        for name,key,value in (('execution.json','child_exit_code',False),('execution.json','timeout_seconds',181),('stage-result.json','package_id','another')):
            p=self.outer/name;raw=p.read_bytes();row=cli.load(p);row[key]=value;cli.write(p,row)
            with self.subTest(key=key),self.assertRaises(ValueError):recovery.origin_terminal(self.c,self.outer,self.manifest,self.request)
            p.write_bytes(raw)


if __name__=='__main__':unittest.main()
