"""Historical evidence must survive zero-block reclamation, including faults."""
import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_project_storage as storage

@unittest.skipUnless(sys.platform=='darwin','Darwin zero-block reclamation')
class LegacyStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.capture=self.root/'capture';self.capture.mkdir()
        self.raw=self.capture/'readback.bin';self.data=b'A'*4096+bytes(4096*256)+b'Z'*31
        self.raw.write_bytes(self.data)
        self.evidence=self.capture/'evidence.json'
        self.evidence.write_text(json.dumps(dict(output_sha256=hashlib.sha256(self.data).hexdigest(),transport=dict(output_bytes=len(self.data)))))
        self.metadata=self.evidence.read_bytes()

    def test_real_reclamation_retains_bytes_inode_and_historical_metadata(self):
        before=self.raw.stat();r=storage.reclaim(self.raw,self.root/'receipt.json',apply=True)
        self.assertTrue(r['passed']);self.assertGreater(r['allocated_reclaimed'],0)
        self.assertEqual(self.raw.read_bytes(),self.data);self.assertEqual(self.raw.stat().st_ino,before.st_ino)
        self.assertEqual(self.raw.stat().st_mtime_ns,before.st_mtime_ns)
        self.assertEqual(self.evidence.read_bytes(),self.metadata)
        self.assertFalse((self.capture/'artifacts.json').exists());self.assertFalse(r['raw_deleted'])

    def test_bad_anchor_never_punches_or_deletes(self):
        self.raw.write_bytes(b'B'+self.data[1:])
        with patch('fcntl.fcntl') as punch,self.assertRaisesRegex(ValueError,'historical evidence'):
            storage.reclaim(self.raw,self.root/'receipt.json',apply=True)
        punch.assert_not_called();self.assertEqual(self.raw.read_bytes(),b'B'+self.data[1:])
        self.assertFalse(json.loads((self.root/'receipt.json').read_text())['passed'])

    def test_symlink_hardlink_and_receipt_alias_are_rejected(self):
        alias=self.root/'alias';alias.symlink_to(self.capture,target_is_directory=True)
        with self.assertRaises(ValueError):storage.reclaim(alias/'readback.bin',self.root/'a.json',apply=True)
        with self.assertRaises(ValueError):storage.reclaim(self.raw,alias/'receipt.json',apply=True)
        os.link(self.raw,self.root/'other')
        with self.assertRaises(ValueError):storage.reclaim(self.raw,self.root/'b.json',apply=True)
        self.assertEqual(self.raw.read_bytes(),self.data)

    def test_plan_and_failure_keep_bytes_and_receipts(self):
        r=storage.reclaim(self.raw,self.root/'plan.json');self.assertEqual(r['allocated_reclaimed'],0)
        with patch('fcntl.fcntl',side_effect=OSError('injected failure')),self.assertRaises(OSError):
            storage.reclaim(self.raw,self.root/'failed.json',apply=True)
        self.assertEqual(self.raw.read_bytes(),self.data)
        with self.assertRaises(ValueError):storage.reclaim(self.raw,self.root/'plan.json',apply=True)

    def test_batched_input_uses_historical_transport_headers(self):
        p=self.capture/'input.bin';p.write_bytes(self.data)
        self.evidence.write_text(json.dumps(dict(input_sha256=hashlib.sha256(self.data).hexdigest(),
            transport=dict(input_bytes=len(self.data)+4,cases=2),
            logical_input_hash='uint32 total count followed by all ordered program words; per-dispatch headers excluded',
            dispatches=[dict(transport=dict(input_bytes=8,cases=1)),dict(transport=dict(input_bytes=len(self.data)-4,cases=1))])))
        r=storage.reclaim(p,self.root/'input.json',apply=True)
        self.assertTrue(r['passed']);self.assertEqual(p.read_bytes(),self.data)

    def test_changed_zero_range_stops_before_punch(self):
        original=storage.scan
        def changed(*args):
            result=original(*args)
            with self.raw.open('r+b') as stream:stream.seek(4096);stream.write(b'X')
            return result
        with patch.object(storage,'scan',side_effect=changed),patch('fcntl.fcntl') as punch,self.assertRaisesRegex(ValueError,'changed during scan'):
            storage.reclaim(self.raw,self.root/'receipt.json',apply=True)
        punch.assert_not_called()

    def test_later_chunk_written_during_apply_is_never_punched(self):
        import fcntl
        self.data=b'A'*4096+bytes(3*1024**2)+b'END';self.raw.write_bytes(self.data)
        self.evidence.write_text(json.dumps(dict(output_sha256=hashlib.sha256(self.data).hexdigest(),transport=dict(output_bytes=len(self.data)))))
        original=fcntl.fcntl;calls=[]
        def racing(fd,command,arg):
            calls.append(arg);result=original(fd,command,arg)
            if len(calls)==1:
                with self.raw.open('r+b') as f:f.seek(4096+1024**2);f.write(b'NEW DATA')
            return result
        with patch('fcntl.fcntl',side_effect=racing),self.assertRaisesRegex(ValueError,'zero range changed'):
            storage.reclaim(self.raw,self.root/'receipt.json',apply=True)
        self.assertEqual(len(calls),1)
        with self.raw.open('rb') as f:f.seek(4096+1024**2);self.assertEqual(f.read(8),b'NEW DATA')

    def test_sweep_excludes_nested_worktree_and_resumes_without_touching_metadata(self):
        import time
        legacy=self.root/'research/portable-build';legacy.mkdir(parents=True)
        self.capture.rename(legacy/'old');self.capture=legacy/'old';self.raw=self.capture/'readback.bin'
        os.utime(self.raw,(time.time()-90000,time.time()-90000))
        nested=legacy/'nested';nested.mkdir();(nested/'.git').write_text('gitdir: elsewhere')
        (nested/'input.bin').write_bytes(b'untouched')
        receipts=self.root/'receipts'
        with patch.object(storage,'ensure_idle'),patch.object(storage,'ensure_closed'):
            result=storage.sweep(self.root,receipts,apply=True)
            self.assertEqual(result['files'],1);self.assertGreater(result['reclaimed_bytes'],0)
            second=storage.sweep(self.root,receipts,apply=True)
        self.assertEqual((nested/'input.bin').read_bytes(),b'untouched')
        self.assertEqual(self.raw.read_bytes(),self.data)
        self.assertTrue(any('Worktree' in r['reason'] for r in second['skipped']))

if __name__=='__main__':unittest.main()
