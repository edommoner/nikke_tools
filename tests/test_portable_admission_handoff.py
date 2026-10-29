"""Synthetic full handoff contracts; no claim, driver, compiler or GPU calls."""
import copy,json,runpy,struct,sys,tempfile,unittest,zipfile
from pathlib import Path,PureWindowsPath
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
from portable_admission_handoff import Handoff
import portable_admission_snapshot as snap
from portable_admission_prepare import SCHEMA
from portable_linked_artifact import key
from portable_phase_audit import Journal
from test_portable_device_linker import cubin
cli=SimpleNamespace(**runpy.run_path(str(ROOT/'scripts/nikke_gpu.py')))


class HandoffTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.base=Path(t.name).resolve()
        self.sources=self.base/'sources';self.sources.mkdir();self.out=self.base/'out';self.out.mkdir()
        self.owner=self.sources/'owner';self.controller=self.sources/'controller';self.tx=self.sources/'tx';self.link=self.sources/'link'
        for p in (self.owner,self.controller,self.tx,self.link):p.mkdir()
        self.input=struct.pack('<III',1,9,10);self.cuda=b'#include "fixed.h"\nvoid portableEvents() {}\n';self.image=cubin();self.header=b'// fixed CUDA prelude\n'
        self.golden=dict(input_sha256=snap.digest(self.input),output_sha256='f'*64,
            entries=[dict(name='synthetic',input_sha256=snap.digest(self.input[4:]),native_sha256='e'*64)],
            source_sha256={'gpu/entry.slang':snap.digest(b'shared slang')},generated_normalized={'cuda':'a'*64,'metal':'b'*64})
        self.manifests={}
        for root,role in ((self.owner,'owner'),(self.controller,'controller')):
            (root/'gpu').mkdir();(root/'gpu/entry.slang').write_bytes(b'shared slang')
            m=dict(schema=cli.SCHEMA,suite='fixture',role=role,golden=self.golden,files=[dict(path='gpu/entry.slang',bytes=12,sha256=snap.digest(b'shared slang'))])
            m['package_id']=cli.package_id(m);self.manifests[root]=m;(root/'gpu-package.json').write_text(json.dumps(m))
        self.binding=dict(owner_package_id=self.manifests[self.owner]['package_id'],controller_package_id=self.manifests[self.controller]['package_id'],transaction_nonce='c'*32,input_sha256=snap.digest(self.input),artifact_sha256=snap.digest(self.image),future_capture=str(self.base/'future'))
        self.input_receipt=cli.transport_input_receipt(self.manifests[self.owner],self.input,2)
        transaction=dict(package_id=self.binding['owner_package_id'],nonce='c'*32,backend='cuda',gpu_capture=self.binding['future_capture'],package_root=str(self.owner),transaction=str(self.tx),input=self.input_receipt,host={'fixture':True},manifest_sha256=snap.digest((self.owner/'gpu-package.json').read_bytes()))
        (self.tx/'transaction.json').write_text(json.dumps(transaction));(self.tx/'input.bin').write_bytes(self.input)
        (self.link/'generated.cu').write_bytes(self.cuda);(self.link/'jit-linked.cubin').write_bytes(self.image);(self.link/'fixed.h').write_bytes(self.header)
        identity=dict(schema=1,provider='saved-module-jit-cubin',artifact='cubin',source_sha256=snap.digest(self.cuda),headers={str(self.link/'fixed.h'):snap.digest(self.header)},source_closure=self.golden['source_sha256'],generated_normalized=self.golden['generated_normalized'])
        receipt=dict(identity=identity,key=key(identity),artifact_bytes=len(self.image),artifact_sha256=snap.digest(self.image),enabled=True,reused=True)
        rows=[]
        for path in sorted(self.sources.rglob('*'),key=str):
            if path.is_file():rows.append(dict(root=str(path.parent),path=path.name,bytes=path.stat().st_size,sha256=snap.digest(path.read_bytes())))
        self.cert=dict(schema=SCHEMA,binding=self.binding,owner_root=str(self.owner),transaction=str(self.tx),owner_manifest_sha256=transaction['manifest_sha256'],golden_sha256=snap.digest(snap.canonical(self.golden)),request={'capture':str(self.link)},
            input_source=str(self.tx/'input.bin'),artifact_source=str(self.link/'jit-linked.cubin'),linked_receipt=receipt,
            staged=dict(package_id=self.binding['owner_package_id'],transaction_nonce='c'*32,transaction=str(self.tx),transaction_sha256=snap.digest((self.tx/'transaction.json').read_bytes()),host=transaction['host'],input=self.input_receipt,all_native_preflight_verified=True,calculation_verified=False,gpu_calls=0),read_set_files=len(rows),read_set_sha256=snap.digest(snap.canonical(rows)),preparation_verified=True,execution_admitted=False,calculation_verified=False,gpu_calls=0,compiler_calls=0,native_battle_calls=0,driver_load_calls=0)
        self.rows=rows
    def freeze(self,edit=None):
        cert=copy.deepcopy(self.cert);rows=copy.deepcopy(self.rows)
        if edit:edit(cert,rows)
        path=self.out/'evidence/certificate.json';path.parent.mkdir();path.write_text(json.dumps(cert));raw=path.read_bytes();self.cert_sha=snap.digest(raw)
        rows.append(dict(root=str(path.parent),path=path.name,bytes=len(raw),sha256=self.cert_sha))
        result=snap.freeze(dict(schema=snap.INVENTORY,binding=self.binding,files=rows),self.out/'snapshot.zip');self.sha=result['snapshot_sha256'];return result
    def reader(self,**kwargs):
        args=dict(certificate_sha256=self.cert_sha,expected_binding=self.binding,expected_suite='fixture',expected_golden=self.golden,consumer_package_id='9'*64);args.update(kwargs)
        return Handoff(cli,self.out/'snapshot.zip',self.sha,**args)
    def test_verified_reads_use_only_archive_and_public_views_cannot_change_binding(self):
        self.freeze()
        import shutil
        shutil.rmtree(self.sources)
        with self.reader() as handoff:
            self.assertEqual(handoff.read_input(),(self.input,2))
            image,receipt=handoff.image_for_source(self.cuda);self.assertEqual(image,self.image)
            cert=handoff.certificate;cert['binding']['transaction_nonce']='0'*32
            receipt['artifact_sha256']='0'*64
            self.assertEqual(handoff.certificate['binding'],self.binding)
            self.assertEqual(handoff.summary()['consumer_package_id'],'9'*64)
            self.assertNotEqual(handoff.summary()['consumer_package_id'],self.binding['controller_package_id'])
            self.assertEqual(handoff.image_for_source(self.cuda)[1]['artifact_sha256'],self.binding['artifact_sha256'])
        with self.assertRaises(RuntimeError):handoff.read_input()
        with self.assertRaises(RuntimeError):
            with handoff:pass
    def test_external_anchor_golden_and_suite_mismatches_rejected(self):
        self.freeze()
        for args in (dict(certificate_sha256='0'*64),dict(expected_binding=dict(self.binding,transaction_nonce='0'*32)),dict(expected_suite='other'),dict(expected_golden=dict(self.golden,output_sha256='0'*64))):
            with self.subTest(args=args),self.assertRaises((ValueError,KeyError)):
                with self.reader(**args):pass
    def test_certificate_scope_and_transaction_mismatches_rejected_even_with_new_anchor(self):
        self.freeze(lambda cert,rows:cert.update(execution_admitted=True))
        with self.assertRaisesRegex(ValueError,'certificate mismatch'):
            with self.reader():pass
    def test_read_set_omission_is_not_hidden_by_reanchoring_archive(self):
        self.freeze(lambda cert,rows:rows.pop())
        with self.assertRaisesRegex(ValueError,'certificate mismatch'):
            with self.reader():pass
    def test_foreign_transaction_nonce_rejected(self):
        self.freeze(lambda cert,rows:cert['staged'].update(transaction_nonce='d'*32))
        with self.assertRaisesRegex(ValueError,'transaction binding'):
            with self.reader():pass
    def test_provider_uses_existing_callback_once_and_forbids_compiler_without_dispatch(self):
        self.freeze();source=self.base/'live.cu';source.write_bytes(self.cuda)
        import portable_backend
        original=portable_backend.compile_cuda_source
        with self.reader() as handoff:
            with handoff.saved_provider('cuda',Journal(self.base/'phases.jsonl')):
                image,receipt=portable_backend.compile_cuda_source(source,artifact_kind='cubin')
                self.assertEqual(image,self.image);self.assertEqual(source.with_suffix('.cubin').read_bytes(),self.image)
                with self.assertRaisesRegex(RuntimeError,'compiler forbidden'):portable_backend.compile_cuda_artifact()
            self.assertIs(portable_backend.compile_cuda_source,original)
            with self.assertRaises(RuntimeError):
                with handoff.saved_provider('cuda',Journal(self.base/'again.jsonl')):pass
        rows=[json.loads(line) for line in (self.base/'phases.jsonl').read_text().splitlines()]
        self.assertEqual(rows[0]['stage'],'prepared_handoff');self.assertFalse(rows[0]['execution_admitted'])
        self.assertFalse(any(r['stage'].startswith('nvrtc') for r in rows))
    def test_existing_shared_executor_consumes_provider_with_cpu_transport_double(self):
        self.freeze();source=self.base/'live.cu';source.write_bytes(self.cuda)
        metal=self.base/'live.metal';metal.write_bytes(b'paired source fixture')
        (self.base/'research/portable-build').mkdir(parents=True)
        import portable_backend
        calls=[]
        def cpu_transport(path,entry,packed,output_bytes,count):
            calls.append((entry,packed,output_bytes,count))
            image,_=portable_backend.compile_cuda_source(path,artifact_kind='cubin')
            self.assertEqual(image,self.image)
            return struct.pack('<I',123),dict(command_status='completed',cases=count)
        # Only the OS transport and code-generation seams are doubles; execute
        # itself is the unchanged common function. Its synthetic evidence is
        # intentionally never exported as a real GPU proof.
        with self.reader() as handoff,patch.object(portable_backend,'ROOT',self.base),patch.object(portable_backend,'build',return_value=({'cuda':source,'metal':metal},self.golden['source_sha256'])),patch.object(portable_backend,'resident_plan',return_value=None),patch.object(portable_backend,'source_hashes',return_value=self.golden['source_sha256']),patch.object(portable_backend,'execute_cuda',side_effect=cpu_transport):
            with handoff.saved_provider('cuda',Journal(self.base/'shared-phases.jsonl')):
                packed,words=handoff.read_input()
                raw,_=portable_backend.execute('gpu/entry.slang','portableEvents',packed,words,1,'cuda')
            self.assertEqual(raw,struct.pack('<I',123));self.assertEqual(calls,[('portableEvents',self.input,4,1)])
            summary=handoff.summary();self.assertFalse(summary['execution_admitted']);self.assertFalse(summary['calculation_verified']);self.assertEqual(summary['gpu_calls'],0)
    def test_typed_zero_counters_do_not_accept_boolean_false(self):
        self.freeze(lambda cert,rows:cert.update(compiler_calls=False))
        with self.assertRaisesRegex(ValueError,'certificate mismatch'):
            with self.reader():pass
    def test_provider_rejects_different_actual_cuda_and_restores_callback(self):
        self.freeze();source=self.base/'live.cu';source.write_bytes(self.cuda+b'changed')
        import portable_backend
        original=portable_backend.compile_cuda_source
        with self.reader() as handoff:
            with self.assertRaisesRegex(ValueError,'exact CUDA bytes'):
                with handoff.saved_provider('cuda',Journal(self.base/'phases.jsonl')):portable_backend.compile_cuda_source(source,artifact_kind='cubin')
        self.assertIs(portable_backend.compile_cuda_source,original);self.assertFalse(source.with_suffix('.cubin').exists())
    def test_no_op_provider_is_not_success(self):
        self.freeze()
        with self.reader() as handoff:
            with self.assertRaisesRegex(ValueError,'exactly one'):
                with handoff.saved_provider('cuda',Journal(self.base/'phases.jsonl')):pass
    def test_header_receipt_mismatch_rejected(self):
        def corrupt(cert,rows):
            receipt=cert['linked_receipt'];receipt['identity']['headers'][str(self.link/'fixed.h')]='0'*64
            receipt['key']=key(receipt['identity'])
        self.freeze(corrupt)
        with self.assertRaisesRegex(ValueError,'header changed'):
            with self.reader():pass
    def test_linked_image_size_mismatch_is_rejected(self):
        self.freeze(lambda cert,rows:cert['linked_receipt'].update(artifact_bytes=len(self.image)+1))
        with self.assertRaisesRegex(ValueError,'CUBIN changed'):
            with self.reader():pass
    def test_caught_provider_failure_cannot_turn_into_success_or_a_second_attempt(self):
        self.freeze();source=self.base/'live.cu';source.write_bytes(self.cuda)
        import portable_backend
        with self.reader() as handoff:
            with self.assertRaisesRegex(ValueError,'exactly one'):
                with handoff.saved_provider('cuda',Journal(self.base/'phases.jsonl')):
                    callback=portable_backend.compile_cuda_source
                    with self.assertRaisesRegex(ValueError,'One explicit'):callback(source,artifact_kind='ptx')
                    with self.assertRaisesRegex(ValueError,'One explicit'):callback(source,artifact_kind='cubin')
            with self.assertRaisesRegex(RuntimeError,'not active'):callback(source,artifact_kind='cubin')
        self.assertFalse(source.with_suffix('.cubin').exists())
    def test_package_source_omission_rejected_after_readset_is_reanchored(self):
        def corrupt(cert,rows):
            rows[:]=[r for r in rows if not (r['root']==str(self.owner/'gpu') and r['path']=='entry.slang')]
            cert['read_set_files']=len(rows);cert['read_set_sha256']=snap.digest(snap.canonical(rows))
        self.freeze(corrupt)
        with self.assertRaisesRegex(ValueError,'closure incomplete'):
            with self.reader():pass
    def test_archive_mutation_after_use_still_rejected(self):
        self.freeze()
        with self.assertRaisesRegex(ValueError,'during use'):
            with self.reader() as handoff:
                self.assertEqual(handoff.read_input(),(self.input,2))
                with (self.out/'snapshot.zip').open('ab') as stream:stream.write(b'changed')
    def test_windows_origin_records_can_be_consumed_without_windows_paths_or_sdk(self):
        self.freeze()
        def convert(value):
            if isinstance(value,str) and value.startswith(str(self.base)):
                return str(PureWindowsPath('C:/frozen')/Path(value).relative_to(self.base).as_posix())
            if isinstance(value,dict):return {convert(k):convert(v) for k,v in value.items()}
            if isinstance(value,list):return [convert(v) for v in value]
            return value
        with zipfile.ZipFile(self.out/'snapshot.zip') as archive:
            payload={name:archive.read(name) for name in archive.namelist()}
        meta=convert(json.loads(payload['manifest.json']))
        cert=convert(self.cert);self.binding=convert(self.binding)
        cert['linked_receipt']['key']=key(cert['linked_receipt']['identity'])
        transaction_row=next(r for r in meta['files'] if r['path']=='transaction.json')
        tx=snap.canonical(convert(json.loads(payload[transaction_row['blob']])))
        transaction_row.update(bytes=len(tx),sha256=snap.digest(tx),blob='blobs/'+snap.digest(tx));payload[transaction_row['blob']]=tx
        cert['staged']['transaction_sha256']=snap.digest(tx)
        trace=[{k:r[k] for k in ('root','path','bytes','sha256')} for r in meta['files'] if r['path']!='certificate.json']
        trace.sort(key=lambda r:str(PureWindowsPath(r['root'])/r['path']))
        cert['read_set_sha256']=snap.digest(snap.canonical(trace))
        raw=snap.canonical(cert);self.cert_sha=snap.digest(raw)
        row=next(r for r in meta['files'] if r['path']=='certificate.json')
        row.update(bytes=len(raw),sha256=self.cert_sha,blob='blobs/'+self.cert_sha);payload[row['blob']]=raw
        windows=self.out/'windows.zip'
        with zipfile.ZipFile(windows,'x') as archive:
            archive.writestr('manifest.json',snap.canonical(meta))
            for name in sorted({r['blob'] for r in meta['files']}):archive.writestr(name,payload[name])
        import shutil
        shutil.rmtree(self.sources)
        with Handoff(cli,windows,snap.file_sha(windows),certificate_sha256=self.cert_sha,expected_binding=self.binding,expected_suite='fixture',expected_golden=self.golden,consumer_package_id='9'*64) as handoff:
            self.assertEqual(handoff.read_input(),(self.input,2));self.assertEqual(handoff.image_for_source(self.cuda)[0],self.image)


if __name__=='__main__':unittest.main()
