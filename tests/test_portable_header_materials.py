"""Complete an older missing dependency without rewriting its source evidence."""
import json,sys,unittest,zipfile
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_header_materials as materials
import portable_admission_snapshot as snap
from portable_admission_handoff import Handoff
import test_portable_admission_handoff as fixture


class HeaderMaterialsTests(unittest.TestCase):
    def setUp(self):
        f=fixture.HandoffTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f
        f.rows[:]=[r for r in f.rows if r['path']!='fixed.h']
        f.cert.update(read_set_files=len(f.rows),read_set_sha256=snap.digest(snap.canonical(f.rows)));f.freeze()
        def verify(root):
            m=fixture.cli.load(root/'gpu-package.json');fixture.cli.check_records(root,m['files'])
            if fixture.cli.package_id(m)!=m['package_id']:raise ValueError('Fixture package changed')
            return m
        self.cli=SimpleNamespace(**{**vars(fixture.cli),'ROOT':f.controller,'verify_package':verify})
        self.out=f.base/'materials';self.before=(f.out/'snapshot.zip').read_bytes()
    def create(self,**kwargs):
        f=self.f
        return materials.create(self.cli,f.out/'snapshot.zip',f.sha,f.cert_sha,f.binding,self.out,**kwargs)
    def reader(self,descriptor):
        f=self.f
        return Handoff(self.cli,f.out/'snapshot.zip',f.sha,certificate_sha256=f.cert_sha,expected_binding=f.binding,expected_suite='fixture',expected_golden=f.golden,consumer_package_id=f.manifests[f.controller]['package_id'],header_materials=descriptor)
    def test_missing_header_stays_missing_in_original_and_supplement_is_complete(self):
        with self.assertRaisesRegex(ValueError,'Frozen source absent'):
            with self.f.reader():pass
        result=self.create();self.assertTrue(result['complete_handoff_bytes_verified']);self.assertFalse(result['execution_admitted']);self.assertFalse(result['calculation_verified'])
        (self.f.link/'fixed.h').unlink()
        with self.reader(result['descriptor']) as reader:
            self.assertEqual(reader.read_input(),(self.f.input,2));self.assertEqual(reader.image_for_source(self.f.cuda)[0],self.f.image)
        self.assertEqual((self.f.out/'snapshot.zip').read_bytes(),self.before)
        with self.assertRaises(FileExistsError):self.create()
        self.assertFalse(Path(self.f.binding['future_capture']).exists())
    def test_wrong_current_header_cannot_replace_authenticated_dependency(self):
        (self.f.link/'fixed.h').write_bytes(b'wrong SDK version')
        with self.assertRaisesRegex(ValueError,'expected SHA'):self.create()
        self.assertTrue((self.out/'failure.json').exists());self.assertFalse((self.out/'result.json').exists())
        self.assertEqual((self.f.out/'snapshot.zip').read_bytes(),self.before)
    def test_explicit_matching_source_may_have_different_local_origin(self):
        old=str(self.f.link/'fixed.h');(self.f.link/'fixed.h').unlink()
        sdk=self.f.base/'local-sdk';sdk.mkdir();p=sdk/'same.h';p.write_bytes(self.f.header)
        result=self.create(sources={old:str(p)})
        p.unlink()
        with self.reader(result['descriptor']) as reader:self.assertEqual(reader.read_input()[0],self.f.input)
    def test_different_base_cannot_reuse_valid_header_materials(self):
        result=self.create();descriptor=result['descriptor']
        with zipfile.ZipFile(descriptor['snapshot']) as archive:data={n:archive.read(n) for n in archive.namelist()}
        manifest=json.loads(data['manifest.json']);meta=json.loads(data['blobs/'+descriptor['manifest_sha256']]);meta['base_certificate_sha256']='0'*64
        raw=snap.canonical(meta);new=snap.digest(raw)
        for row in manifest['files']:
            if row['blob']=='blobs/'+descriptor['manifest_sha256']:row.update(bytes=len(raw),sha256=new,blob='blobs/'+new)
        data['blobs/'+new]=raw
        forged=self.out/'foreign.zip'
        with zipfile.ZipFile(forged,'x') as archive:
            archive.writestr('manifest.json',snap.canonical(manifest))
            for name in sorted({r['blob'] for r in manifest['files']}):archive.writestr(name,data[name])
        with self.assertRaisesRegex(ValueError,'base/scope'):
            with self.reader(dict(snapshot=str(forged),sha256=snap.file_sha(forged),manifest_sha256=new)):pass
    def test_materials_must_remain_immutable_during_use(self):
        result=self.create();desc=result['descriptor']
        with self.assertRaisesRegex(ValueError,'during use'):
            with self.reader(desc):
                with Path(desc['snapshot']).open('ab') as stream:stream.write(b'changed')


class HeaderAuthorityTests(unittest.TestCase):
    def setUp(self):
        import test_portable_admission_authority as fixtures
        f=fixtures.AuthorityTests();f.omit_header=True;f.setUp();self.addCleanup(f.doCleanups);self.f=f
        self.result=materials.create(f.cli,f.stage/'proof/snapshot.zip',f.f.sha,f.f.cert_sha,f.f.binding,f.f.base/'header-materials')
    def authenticate(self):
        import portable_admission_authority as authority
        f=self.f
        return authority.authenticate(f.cli,f.f.controller,f.stage,expected_binding=f.f.binding,snapshot_sha256=f.f.sha,certificate_sha256=f.f.cert_sha,out=f.f.base/'authority',header_materials=self.result['descriptor'])
    def test_authority_and_claim_bind_header_materials_without_gpu(self):
        import portable_admission_authority as authority
        checked=self.authenticate();self.assertEqual(checked.receipt['header_materials'],self.result['descriptor'])
        record=authority.claim(self.f.cli,checked)
        self.assertEqual(record['authority_sha256'],snap.file_sha(self.f.f.base/'authority/authority.json'))
        self.assertFalse(Path(self.f.f.binding['future_capture']).exists())
    def test_changed_materials_prevent_claim_and_preserve_original_attempt(self):
        import portable_admission_authority as authority
        checked=self.authenticate()
        with Path(self.result['descriptor']['snapshot']).open('ab') as stream:stream.write(b'changed')
        with self.assertRaisesRegex(ValueError,'header materials changed'):authority.claim(self.f.cli,checked)
        self.assertFalse((self.f.f.tx/'gpu-execution-claimed.json').exists())


if __name__=='__main__':unittest.main()
