"""Cache compression preserves real bytes/keys and refuses unsafe candidates."""
import base64,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_cache_fs_compression as fs
from portable_generation_cache import key

def entry(folder):
    identity=dict(kind='paired-resident-slang-generation');payload=b'public-test-artifact';row=dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),base64=base64.b64encode(payload).decode());p=folder/(key(identity)+'.json');p.write_text(json.dumps(dict(schema=1,identity=identity,key=key(identity),artifacts={n:row for n in ('cuda','metal','cuda-reflection','metal-reflection')})));return p

class CompressionTests(unittest.TestCase):
    def setUp(self):
        # Integrity/claim tests run on Windows too, without pretending to
        # measure its filesystem allocation or requiring compression rights.
        allocation=patch.object(fs,'allocation',side_effect=lambda p:p.stat().st_size)
        allocation.start();self.addCleanup(allocation.stop)
        if sys.platform!='darwin':
            sync=patch.object(fs.os,'fsync');sync.start();self.addCleanup(sync.stop)

    def test_nonmac_public_command_refuses_before_filesystem_io(self):
        with patch.object(fs.sys,'platform','win32'),patch.object(fs.Path,'mkdir') as mkdir,self.assertRaisesRegex(ValueError,'requires macOS'):
            fs.run(Path('unused'),Path('unused-output'),apply=True)
        mkdir.assert_not_called()
    def test_byte_exact_atomic_replacement_with_unchanged_cache_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=entry(root);dest=root/'stage'/source.name;dest.parent.mkdir();before=source.read_bytes()
            state={'packed':False}
            def packed(a,b):b.write_bytes(a.read_bytes());state['packed']=True
            is_packed=lambda p:state['packed'] and (p==dest or p==source and not dest.exists())
            with patch.object(fs,'pack',side_effect=packed),patch.object(fs,'compressed',side_effect=is_packed),patch.object(fs,'allocation',side_effect=lambda p:1024 if is_packed(p) else 4096):
                r=fs.compress_one(source,dest)
            self.assertEqual(source.read_bytes(),before);self.assertEqual(r['status'],'compressed');self.assertTrue(r['logical_bytes_equal']);self.assertFalse(source.with_suffix('.claim').exists())
    def test_truncated_copy_is_detected_before_original_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=entry(root);dest=root/'stage'/source.name;dest.parent.mkdir();before=source.read_bytes()
            with patch.object(fs,'pack',side_effect=lambda a,b:b.write_bytes(b'')),self.assertRaises(ValueError):fs.compress_one(source,dest)
            self.assertEqual(source.read_bytes(),before);self.assertTrue(dest.exists());self.assertFalse(source.with_suffix('.claim').exists())
    def test_valid_but_different_cache_payload_cannot_replace_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=entry(root);dest=root/'stage'/source.name;dest.parent.mkdir();before=source.read_bytes()
            def changed(a,b):
                value=json.loads(a.read_bytes());payload=b'other-artifact'
                for row in value['artifacts'].values():row.update(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),base64=base64.b64encode(payload).decode())
                b.write_text(json.dumps(value))
            with patch.object(fs,'pack',side_effect=changed),self.assertRaises(ValueError):fs.compress_one(source,dest)
            self.assertEqual(source.read_bytes(),before)
    def test_live_or_stale_claim_is_never_stolen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=entry(root);claim=source.with_suffix('.claim');claim.write_bytes(b'owner');before=source.read_bytes()
            with patch.object(fs,'pack') as pack,self.assertRaises(RuntimeError):fs.compress_one(source,root/'stage')
            pack.assert_not_called();self.assertEqual(claim.read_bytes(),b'owner');self.assertEqual(source.read_bytes(),before)
    def test_wrong_filename_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=entry(root);source.rename(root/('f'*64+'.json'))
            with self.assertRaises(ValueError):fs.checked(root/('f'*64+'.json'))
    def test_link_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=entry(root);link=root/('0'*64+'.json')
            try:link.symlink_to(source)
            except OSError:self.skipTest('Symlink creation unavailable on this host')
            with self.assertRaises(ValueError):fs.checked(link)

if __name__=='__main__':unittest.main()
