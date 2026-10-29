"""Synthetic Windows-branch receipts; real shared parsers, no real Job or GPU."""
import copy,json,sys,unittest,zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_admission_authority as authority
import portable_admission_snapshot as snap
from portable_staged_preflight import host
from windows_validation_observer import compare_snapshots
import test_portable_admission_handoff as fixture
original_cli=fixture.cli


class AuthorityTests(unittest.TestCase):
    def setUp(self):
        f=fixture.HandoffTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f;self.consumer=f.sources/'consumer';(self.consumer/'gpu').mkdir(parents=True)
        (self.consumer/'gpu/entry.slang').write_bytes(b'shared slang')
        self.config_patch=patch.dict(original_cli.verify_package.__globals__['SUITES'],{'authority-fixture':dict(source='gpu/entry.slang',golden='golden.json')})
        self.config_patch.start();self.addCleanup(self.config_patch.stop)
        self.cli=SimpleNamespace(**{**vars(original_cli),'ROOT':self.consumer})
        (f.controller/'scripts').mkdir();(f.controller/'scripts/run-gpu-packet.py').write_bytes((ROOT/'scripts/run-gpu-packet.py').read_bytes())
        manifests={}
        for root,role in ((f.owner,'owner'),(f.controller,'controller'),(self.consumer,'consumer')):
            (root/'golden.json').write_text(json.dumps(f.golden))
            names=['gpu/entry.slang','golden.json']+(['scripts/run-gpu-packet.py'] if root==f.controller else [])
            m=dict(schema=self.cli.SCHEMA,suite='authority-fixture',role=role,golden=f.golden,files=self.cli.file_records(root,names));m['package_id']=self.cli.package_id(m)
            (root/'gpu-package.json').write_text(json.dumps(m));manifests[root]=m
        f.binding.update(owner_package_id=manifests[f.owner]['package_id'],controller_package_id=manifests[f.controller]['package_id'])
        f.input_receipt=self.cli.transport_input_receipt(manifests[f.owner],f.input,2)
        transaction=json.loads((f.tx/'transaction.json').read_bytes());transaction.update(package_id=f.binding['owner_package_id'],input=f.input_receipt,host=host(self.cli),manifest_sha256=snap.digest((f.owner/'gpu-package.json').read_bytes()))
        (f.tx/'transaction.json').write_text(json.dumps(transaction))
        (f.owner/'gpu-claimed-cuda.json').write_text(json.dumps(dict(package_id=f.binding['owner_package_id'],capture=f.binding['future_capture'],transaction=str(f.tx),transaction_nonce=f.binding['transaction_nonce'])))
        f.cert.update(owner_manifest_sha256=transaction['manifest_sha256'])
        f.cert['staged'].update(package_id=f.binding['owner_package_id'],input=f.input_receipt,host=transaction['host'],transaction_sha256=snap.digest((f.tx/'transaction.json').read_bytes()))
        self.stage=f.base/'stage';self.stage.mkdir();f.out=self.stage/'proof';f.out.mkdir()
        f.rows=[]
        for path in sorted(f.sources.rglob('*'),key=str):
            if path.is_file():f.rows.append(dict(root=str(path.parent),path=path.name,bytes=path.stat().st_size,sha256=snap.digest(path.read_bytes())))
        f.cert.update(read_set_files=len(f.rows),read_set_sha256=snap.digest(snap.canonical(f.rows)))
        self.request=dict(owner_package=str(f.owner),expected_owner_id=f.binding['owner_package_id'],transaction=str(f.tx),linked_package=str(f.base/'linked'),linked_capture=str(f.link),producer_package=str(f.base/'producer'),producer_capture=str(f.base/'producer-proof'))
        f.cert['request']=dict(package=self.request['linked_package'],capture=self.request['linked_capture'],producer_package=self.request['producer_package'],producer_capture=self.request['producer_capture'])
        snapshot=f.freeze()
        with zipfile.ZipFile(f.out/'snapshot.zip') as archive:meta=json.loads(archive.read('manifest.json'))
        (f.out/'inventory.json').write_text(json.dumps(dict(schema=snap.INVENTORY,binding=f.binding,files=[{k:r[k] for k in ('root','path','bytes','sha256')} for r in meta['files']])))
        self.proof=dict(schema='prepared-admission-evidence-v1',binding=f.binding,certificate_sha256=f.cert_sha,snapshot=snapshot,preparation_verified=True,execution_admitted=False,calculation_verified=False,gpu_calls=0,compiler_calls=0,native_battle_calls=0,driver_load_calls=0)
        self.save('proof/result.json',self.proof)
        wrapper=self.cli.module(f.controller/'scripts/run-gpu-packet.py')
        plan=wrapper.recipe(manifests[f.controller]['package_id'],'prepare-admission','cuda',self.stage,f.base/'original',180,self.request);self.save('recipe.json',plan)
        self.save('execution.json',dict(passed=True,timed_out=False,child_exit_code=0,final_child_exit_code=0,below_normal_priority=True,timeout_seconds=179.9,error=None,cleanup_error=None,observation_error=None,wait_completed_unix_ns=1000))
        base=str(authority.base_python());self.save('command.json',dict(base_python=base,argv=[base,str(f.controller/'scripts/run-gpu-packet.py'),'--_child','--capture',str(self.stage)],shell=False,cwd=str(f.controller),timeout_seconds=180))
        self.save('child.json',dict(pid=103,ppid=104,package_id=manifests[f.controller]['package_id'],started_unix_ns=150))
        self.save('job.json',dict(records=[dict(child_pid=103,wrapper_pid=104,pre_gate_verified=True,inspection_error=None,pre_gate=dict(child_pid=103,child_ppid=104,job_members=[103],child_creation_filetime_ticks='identity',observed_unix_ns=200,job_memory_limit_bytes=2147483648),post_wait=dict(child_pid=103,child_ppid=104,job_members=[],child_creation_filetime_ticks='identity',observed_unix_ns=500,job_memory_limit_bytes=2147483648))]))
        (self.stage/'preparation.jsonl').write_text('\n'.join(json.dumps(dict(pid=103,stage='packet_shared_cli',state=state,monotonic_ns=i,wall_time_ns=300+i)) for i,state in enumerate(('entered','returned')))+'\n')
        before=dict(processes=[],service_status='unverified',observed_unix_ns=100);after=dict(processes=[],service_status='unverified',observed_unix_ns=1001)
        self.save('observation.json',dict(before=before,after=after,comparison=compare_snapshots(before,after)))
        self.save('stage-result.json',dict(schema=1,compiler_verified=False,generation_verified=False,cpu_verified=False,smoke_verified=False,full_goal_complete=False,gpu_retries=0,package_id=manifests[f.controller]['package_id'],stage='prepare-admission',bounded_execution_verified=True,stage_verified=True,stage_complete=True,preparation_verified=True,execution_admitted=False,calculation_verified=False,proof_result=self.proof,whole_stage_process_preservation_verified=True,whole_stage_environment_preservation_verified=False))
        (f.controller/'packet-stage-claimed-prepare-admission-cuda.json').write_text(json.dumps(dict(package_id=manifests[f.controller]['package_id'],capture=str(self.stage),created_unix_ns=100)))
        self.proxy=patch.object(authority,'is_windows',return_value=True);self.proxy.start();self.addCleanup(self.proxy.stop)
    def save(self,name,value):(self.stage/name).write_text(json.dumps(value))
    def change(self,name,**value):
        old=self.cli.load(self.stage/name);old.update(value);self.save(name,old)
    def authenticate(self,out=None):
        f=self.f
        return authority.authenticate(self.cli,f.controller,self.stage,expected_binding=f.binding,snapshot_sha256=f.sha,certificate_sha256=f.cert_sha,out=f.base/(out or 'authority'))
    def test_authority_binds_complete_preparation_and_one_claim_preserves_unknown_service(self):
        a=self.authenticate();r=a.receipt
        self.assertTrue(r['authority_verified']);self.assertFalse(r['envelope']['environment_preservation_verified']);self.assertFalse(r['execution_admitted'])
        r['binding']['transaction_nonce']='0'*32;self.assertEqual(a.receipt['binding'],self.f.binding)
        record=authority.claim(self.cli,a)
        self.assertEqual(self.cli.load(self.f.tx/'gpu-execution-claimed.json'),record);self.assertEqual(self.cli.load(self.consumer/'gpu-claimed-cuda.json'),record)
        self.assertEqual(record['protocol'],authority.PROTOCOL);self.assertEqual(record['consumer_package_id'],self.cli.load(self.consumer/'gpu-package.json')['package_id'])
        self.assertFalse(Path(self.f.binding['future_capture']).exists())
        with self.assertRaises(ValueError):authority.claim(self.cli,a)
        with self.assertRaises(ValueError):authority.claim(self.cli,a.receipt)
    def test_original_platform_gate_cannot_be_satisfied_by_a_saved_flag(self):
        with patch.object(authority,'is_windows',return_value=False),self.assertRaisesRegex(ValueError,'original Windows'):self.authenticate()
        self.assertFalse((self.f.base/'authority').exists())
    def test_wrong_external_controller_fails_before_import(self):
        self.f.binding['controller_package_id']='0'*64
        with self.assertRaisesRegex(ValueError,'controller ID'):self.authenticate()
    def test_failed_child_and_boolean_exit_never_create_authority(self):
        self.change('execution.json',child_exit_code=False)
        with self.assertRaisesRegex(ValueError,'bounded CPU'):self.authenticate()
        self.assertFalse((self.f.tx/'gpu-execution-claimed.json').exists())
    def test_incomplete_child_journal_fails_even_if_stage_success_is_true(self):
        rows=(self.stage/'preparation.jsonl').read_text().splitlines();(self.stage/'preparation.jsonl').write_text(rows[0]+'\n')
        with self.assertRaisesRegex(ValueError,'journal incomplete'):self.authenticate()
    def test_wrong_job_cap_fails_shared_job_auditor(self):
        job=self.cli.load(self.stage/'job.json');job['records'][0]['post_wait']['job_memory_limit_bytes']=1073741824;self.save('job.json',job)
        with self.assertRaisesRegex(ValueError,'Job/gate'):self.authenticate()
    def test_late_observation_is_not_environment_preservation(self):
        o=self.cli.load(self.stage/'observation.json');o['after']['observed_unix_ns']=31_000_001_000;self.save('observation.json',o)
        with self.assertRaisesRegex(ValueError,'late'):self.authenticate()
    def test_missing_unrelated_process_is_not_ignored(self):
        o=self.cli.load(self.stage/'observation.json')
        o['before']['processes']=[dict(pid=999,path='unrelated-python',creation_filetime_ticks='creation',role='unrelated')]
        o['comparison']=compare_snapshots(o['before'],o['after']);self.save('observation.json',o)
        with self.assertRaisesRegex(ValueError,'process preservation'):self.authenticate()
        self.assertFalse((self.f.tx/'gpu-execution-claimed.json').exists())
    def test_new_authentication_cannot_replay_a_consumed_original_attempt(self):
        a=self.authenticate();authority.claim(self.cli,a)
        with self.assertRaisesRegex(ValueError,'unconsumed'):self.authenticate('second-authority')
        self.assertFalse(Path(self.f.binding['future_capture']).exists())
    def test_current_host_mismatch_stops_before_claim(self):
        with patch.object(authority,'host',return_value={'different':True}),self.assertRaisesRegex(ValueError,'source host'):self.authenticate()
    def test_snapshot_changed_after_authentication_cannot_claim(self):
        a=self.authenticate()
        with (self.stage/'proof/snapshot.zip').open('ab') as f:f.write(b'changed')
        with self.assertRaisesRegex(ValueError,'snapshot'):authority.claim(self.cli,a)
        self.assertFalse((self.f.tx/'gpu-execution-claimed.json').exists())
    def test_consumer_code_changed_after_authentication_cannot_claim(self):
        a=self.authenticate();(self.consumer/'gpu/entry.slang').write_bytes(b'changed')
        with self.assertRaises(ValueError):authority.claim(self.cli,a)
        self.assertFalse((self.f.tx/'gpu-execution-claimed.json').exists())
    def test_partial_claim_is_retained_and_handle_cannot_retry(self):
        a=self.authenticate();original=authority.exclusive
        def fail(path,value):
            if Path(path)==self.consumer/'gpu-claimed-cuda.json':raise OSError('publish failed')
            return original(path,value)
        with patch.object(authority,'exclusive',side_effect=fail),self.assertRaisesRegex(OSError,'publish failed'):authority.claim(self.cli,a)
        self.assertTrue((self.f.tx/'gpu-execution-claimed.json').exists());self.assertTrue((self.f.base/'authority/claim-failure.json').exists())
        self.assertFalse((self.consumer/'gpu-claimed-cuda.json').exists())
        with self.assertRaises(ValueError):authority.claim(self.cli,a)


if __name__=='__main__':unittest.main()
