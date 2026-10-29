"""Protocol fault injection; fixtures do not claim real staged/CUDA admission."""
import contextlib,copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_admission_prepare as prep
import portable_admission_snapshot as snap
import portable_staged_preflight as staged
import portable_capture_storage as storage


class PreparationTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.base=Path(t.name).resolve()
        self.controller=self.base/'controller';self.owner=self.base/'owner';self.tx=self.base/'transaction'
        self.capture=self.base/'future';self.out=self.base/'out';self.calls=[]
        for p in (self.controller,self.owner,self.tx):p.mkdir()
        self.load=lambda p:json.loads(Path(p).read_text())
        self.package_id=lambda m:snap.digest(snap.canonical({k:v for k,v in m.items() if k!='package_id'}))
        self.manifests={}
        for root in (self.controller,self.owner):
            (root/'scripts').mkdir();(root/'scripts/nikke_gpu.py').write_text('# fixture only\n')
            (root/'source').write_bytes(b'fixture-source')
            rows=[dict(path=n,bytes=(root/n).stat().st_size,sha256=storage.file_digest(root/n)) for n in ('source','scripts/nikke_gpu.py')]
            m=dict(suite='fixture',golden={'input_sha256':snap.digest(b'input')},files=rows);m['package_id']=self.package_id(m)
            (root/'gpu-package.json').write_text(json.dumps(m));self.manifests[root]=m
        self.m=self.manifests[self.owner]
        (self.tx/'transaction.json').write_text(json.dumps(dict(gpu_capture=str(self.capture),backend='cuda')))
        (self.tx/'input.bin').write_bytes(b'input')
        self.image=self.base/'artifact'/'saved.cubin';self.image.parent.mkdir();from test_portable_device_linker import cubin
        self.image.write_bytes(cubin())
        from portable_linked_artifact import key
        sdk=self.base/'sdk';sdk.mkdir();header=sdk/'prelude.h';self.header=header;header.write_bytes(b'// fixed header')
        shader=('#include '+json.dumps(str(header))+'\nvoid portableEvents() {}\n').encode()
        identity=dict(schema=1,provider='saved-module-jit-cubin',artifact='cubin',source_sha256=snap.digest(shader),headers={str(header):snap.digest(header.read_bytes())})
        self.receipt=dict(identity=identity,key=key(identity),artifact_bytes=self.image.stat().st_size,artifact_sha256=snap.digest(self.image.read_bytes()),enabled=True,reused=True)
        self.input=dict(input_words=1,input_sha256=snap.digest(b'input'))
        self.staged=dict(package_id=self.m['package_id'],transaction=str(self.tx),input=self.input,transaction_nonce='c'*32,all_native_preflight_verified=True)
        producer=self.base/'producer-proof';producer.mkdir();(producer/'generated.cu').write_bytes(shader)
        self.request={'package':str(self.base/'linked'),'capture':str(self.base/'link-proof'),'producer_package':str(self.base/'producer'),'producer_capture':str(self.base/'producer-proof')}
        def verify(root):
            m=self.load(root/'gpu-package.json')
            for row in m['files']:
                if storage.file_digest(root/row['path'])!=row['sha256']:raise ValueError('fixture source changed')
            return m
        def module(path):
            self.calls.append('owner_import');path.read_bytes();return self.owner_cli
        def link(m,request):
            self.calls.append('linked');return dict(receipt=copy.deepcopy(self.receipt),artifact=str(self.image))
        def admit(*args):
            self.calls.append('staged');return copy.deepcopy(self.staged)
        self.owner_cli=SimpleNamespace(ROOT=self.owner,load=self.load,forbid_gpu=contextlib.nullcontext,
            saved_linked_admission=link,transport_input_receipt=lambda *args:copy.deepcopy(self.input))
        self.cli=SimpleNamespace(ROOT=self.controller,load=self.load,package_id=self.package_id,
            verify_package=verify,is_development=lambda m:False,compiler_only=lambda m:False,
            forbid_gpu=contextlib.nullcontext,module=module)
        self.patcher=patch.object(staged,'admit',admit);self.patcher.start();self.addCleanup(self.patcher.stop)
    def run_prepare(self):return prep.prepare(self.cli,self.owner,self.m['package_id'],self.tx,self.request,self.out)
    def test_original_audits_called_and_all_sources_frozen_without_execution(self):
        result=self.run_prepare();self.assertEqual(self.calls,['owner_import','staged','linked'])
        self.assertTrue(result['preparation_verified']);self.assertFalse(result['execution_admitted']);self.assertFalse(result['calculation_verified'])
        self.assertFalse(self.capture.exists());self.assertFalse((self.tx/'gpu-execution-claimed.json').exists())
        cert=self.load(self.out/'evidence/certificate.json');inventory=self.load(self.out/'inventory.json')
        with snap.Snapshot(self.out/'snapshot.zip',result['snapshot']['snapshot_sha256']) as reader:
            self.assertEqual(reader.read(self.tx,'input.bin'),b'input')
            self.assertEqual(reader.read(self.header.parent,self.header.name),b'// fixed header')
            self.assertEqual(reader.read(self.image.parent,self.image.name),self.image.read_bytes())
            self.assertEqual(reader.read(self.out/'evidence','certificate.json'),(self.out/'evidence/certificate.json').read_bytes())
        self.assertEqual(cert['read_set_sha256'],snap.digest(snap.canonical(inventory['files'][:-1])))
        with self.assertRaises(FileExistsError):self.run_prepare()
    def stage_request(self):
        return dict(owner_package=str(self.owner),expected_owner_id=self.m['package_id'],transaction=str(self.tx),linked_package=self.request['package'],linked_capture=self.request['capture'],producer_package=self.request['producer_package'],producer_capture=self.request['producer_capture'])
    def test_parent_rejects_forged_execution_scope_and_different_owner(self):
        result=self.run_prepare();request=self.stage_request();controller=self.manifests[self.controller]['package_id']
        self.assertTrue(prep.verified_result(result,self.out,controller,request))
        for key,value in [('gpu_calls',True),('compiler_calls',1),('native_battle_calls',False),('driver_load_calls',1),('execution_admitted',True),('calculation_verified',True)]:
            bad=copy.deepcopy(result);bad[key]=value
            self.assertFalse(prep.verified_result(bad,self.out,controller,request))
        self.assertFalse(prep.verified_result(result,self.out,'0'*64,request))
        self.assertFalse(prep.verified_result(result,self.out,controller,dict(request,expected_owner_id='0'*64)))
        self.assertFalse(prep.verified_result(result,self.out,controller,dict(request,transaction=str(self.base/'other'))))
    def test_parent_authenticates_certificate_and_does_not_accept_a_success_flag(self):
        result=self.run_prepare();request=self.stage_request();controller=self.manifests[self.controller]['package_id']
        for proof in (None,True,dict(preparation_verified=True)):
            self.assertFalse(prep.verified_result(proof,self.out,controller,request))
        cert=self.out/'evidence/certificate.json';value=self.load(cert);value['staged']['transaction_nonce']='d'*32
        cert.write_text(json.dumps(value))
        bad=copy.deepcopy(result);bad['certificate_sha256']=snap.digest(cert.read_bytes())
        self.assertFalse(prep.verified_result(bad,self.out,controller,request))
    def test_external_owner_anchor_rejected_before_import_or_output(self):
        with self.assertRaisesRegex(ValueError,'ID mismatch'):prep.prepare(self.cli,self.owner,'0'*64,self.tx,self.request,self.out)
        self.assertFalse(self.out.exists());self.assertEqual(self.calls,[])
    def test_golden_difference_fails_before_owner_import_and_retains_failure(self):
        self.cli.verify_package=lambda p:dict(self.manifests[p],golden={'different':str(p)})
        with self.assertRaisesRegex(ValueError,'golden'):self.run_prepare()
        self.assertEqual(self.calls,[]);self.assertTrue((self.out/'failure.json').exists());self.assertFalse((self.out/'result.json').exists())
    def test_consumed_claim_and_existing_capture_are_not_removed(self):
        claim=self.tx/'gpu-execution-claimed.json';claim.write_bytes(b'claimed')
        with self.assertRaisesRegex(ValueError,'unconsumed'):self.run_prepare()
        self.assertEqual(claim.read_bytes(),b'claimed');self.assertNotIn('staged',self.calls)
    def test_incomplete_native_and_changed_cubin_never_publish_success(self):
        self.staged['all_native_preflight_verified']=False
        with self.assertRaisesRegex(ValueError,'incomplete'):self.run_prepare()
        self.assertFalse((self.out/'result.json').exists());self.assertTrue((self.out/'failure.json').exists())
    def test_artifact_receipt_mismatch_is_rejected(self):
        self.receipt['artifact_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'CUBIN.*changed'):self.run_prepare()
        self.assertFalse((self.out/'snapshot.zip').exists())
    def test_audit_source_mutation_rejected_when_snapshot_rechecks(self):
        old=self.owner_cli.saved_linked_admission
        def link(*args):
            (self.owner/'source').write_bytes(b'changed');return old(*args)
        self.owner_cli.saved_linked_admission=link
        with self.assertRaisesRegex(ValueError,'changed'):self.run_prepare()
        self.assertTrue((self.out/'failure.json').exists());self.assertFalse((self.out/'result.json').exists())
    def test_new_execution_claim_during_preparation_is_rejected(self):
        old=self.owner_cli.saved_linked_admission
        def claim(*args):
            (self.tx/'gpu-execution-claimed.json').write_bytes(b'other execution');return old(*args)
        self.owner_cli.saved_linked_admission=claim
        with self.assertRaisesRegex(ValueError,'unconsumed'):self.run_prepare()
        self.assertEqual((self.tx/'gpu-execution-claimed.json').read_bytes(),b'other execution')
        self.assertFalse((self.out/'result.json').exists())
    def test_missing_package_reads_are_rejected_even_when_auditor_returns_success(self):
        self.cli.verify_package=lambda p:self.load(p/'gpu-package.json')
        with self.assertRaisesRegex(ValueError,'Incomplete'):self.run_prepare()
        self.assertFalse((self.out/'inventory.json').exists())
    def test_previously_cached_helper_with_different_bytes_is_rejected(self):
        for root in (self.controller,self.owner):(root/'app').mkdir()
        a=self.controller/'app/audit.py';b=self.owner/'app/audit.py';a.write_bytes(b'changed');b.write_bytes(b'original')
        with patch.dict(sys.modules,fixture_cached_audit=SimpleNamespace(__file__=str(a))):
            with self.assertRaisesRegex(ValueError,'Cached audit helper'):self.run_prepare()
        self.assertEqual(self.calls,[])
    def test_future_capture_already_present_stops_before_audits(self):
        self.capture.mkdir();(self.capture/'failure').write_bytes(b'preserve')
        with self.assertRaisesRegex(ValueError,'unconsumed'):self.run_prepare()
        self.assertEqual((self.capture/'failure').read_bytes(),b'preserve');self.assertNotIn('staged',self.calls)
    def test_audit_exception_preserves_original_claim_and_no_success(self):
        original_path=list(sys.path)
        def fail(*args):sys.path.insert(0,'fake');raise RuntimeError('audit failure')
        self.owner_cli.saved_linked_admission=fail
        with self.assertRaisesRegex(RuntimeError,'audit failure'):self.run_prepare()
        self.assertEqual(sys.path,original_path);self.assertTrue((self.out/'failure.json').exists());self.assertFalse(self.capture.exists())


if __name__=='__main__':unittest.main()
