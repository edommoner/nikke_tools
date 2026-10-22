"""Actual APFS zero reclamation plus byte/anchor/failure preservation."""
import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_sparse_raw import sparsify_raw,BLOCK


def check(root,records):
    for record in records:
        p=Path(root)/record['path']
        if p.stat().st_size!=record['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('Artifact mismatch')


@unittest.skipUnless(sys.platform=='darwin','Darwin F_PUNCHHOLE')
class SparseRawTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.capture=self.root/'capture';self.capture.mkdir();self.raw=self.capture/'readback.bin'
        self.payload=b'A'*BLOCK+bytes(BLOCK*32)+b'B'*BLOCK+bytes(BLOCK*5+13)
        self.raw.write_bytes(self.payload)
        e=dict(transport=dict(output_bytes=len(self.payload)),output_sha256=hashlib.sha256(self.payload).hexdigest())
        (self.capture/'evidence.json').write_text(json.dumps(e));(self.capture/'run.json').write_text(json.dumps(dict(status='finished')))
        records=[dict(path=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (self.raw,self.capture/'evidence.json')]
        (self.capture/'artifacts.json').write_text(json.dumps(dict(files=records)));self.metadata={p.name:p.read_bytes() for p in self.capture.iterdir() if p!=self.raw}

    def run_sparse(self,apply=False,name='receipt.json'):return sparsify_raw(self.capture,self.root/name,check,apply=apply)

    def test_actual_reclamation_retains_raw_bytes_path_inode_and_evidence(self):
        before=self.raw.stat();result=self.run_sparse(True)
        self.assertTrue(result['passed']);self.assertEqual(self.raw.read_bytes(),self.payload);self.assertEqual(self.raw.stat().st_ino,before.st_ino)
        self.assertGreater(result['allocated_reclaimed'],0);self.assertEqual(result['zero_range_bytes'],BLOCK*37)
        self.assertEqual({p.name:p.read_bytes() for p in self.capture.iterdir() if p!=self.raw},self.metadata)
        self.assertFalse(result['raw_deleted']);self.assertFalse(result['calculation_verified']);self.assertEqual(result['gpu_calls'],0)
        again=self.run_sparse(True,'again.json');self.assertTrue(again['passed']);self.assertEqual(again['allocated_reclaimed'],0)

    def test_historical_raw_exclusion_uses_existing_evidence_without_rewriting_metadata(self):
        p=self.capture/'artifacts.json';d=json.loads(p.read_text());d['files']=[r for r in d['files'] if r['path']!='readback.bin'];d['raw_included']=False;p.write_text(json.dumps(d));before=p.read_bytes()
        result=self.run_sparse(True);self.assertTrue(result['passed']);self.assertEqual(p.read_bytes(),before);self.assertEqual(self.raw.read_bytes(),self.payload)
        del d['raw_included'];p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.run_sparse(True,'missing-policy.json')

    def test_plan_and_fresh_receipt_guard_do_not_mutate(self):
        before=self.raw.stat();result=self.run_sparse();self.assertTrue(result['passed']);self.assertEqual(result['allocated_reclaimed'],0)
        with self.assertRaises(ValueError):self.run_sparse(True)
        self.assertEqual(self.raw.stat().st_blocks,before.st_blocks);self.assertEqual(self.raw.read_bytes(),self.payload)

    def test_receipt_inside_capture_through_directory_alias_is_rejected(self):
        alias=self.root/'alias';alias.symlink_to(self.capture,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'outside immutable'):sparsify_raw(self.capture,alias/'receipt.json',check,apply=True)
        self.assertFalse((self.capture/'receipt.json').exists());self.assertEqual(self.raw.read_bytes(),self.payload)

    def test_wrong_raw_and_artifact_anchors_stop_before_punch(self):
        with self.raw.open('r+b') as f:f.write(b'Z')
        with patch('fcntl.fcntl') as punch,self.assertRaises(ValueError):self.run_sparse(True)
        punch.assert_not_called();self.assertEqual(self.raw.read_bytes(),b'Z'+self.payload[1:])
        self.assertFalse(json.loads((self.root/'receipt.json').read_text())['passed'])

    def test_incomplete_or_failed_capture_is_rejected_without_mutation(self):
        for status in ['preflight','running','failed']:
            (self.capture/'run.json').write_text(json.dumps(dict(status=status)))
            with patch('fcntl.fcntl') as punch,self.assertRaises(ValueError):self.run_sparse(True,status+'.json')
            punch.assert_not_called()
        self.assertEqual(self.raw.read_bytes(),self.payload)

    def test_symlink_and_hardlink_raw_are_rejected(self):
        moved=self.root/'actual';self.raw.rename(moved);self.raw.symlink_to(moved)
        with self.assertRaises(OSError):self.run_sparse(True)
        self.raw.unlink();os.link(moved,self.raw)
        with self.assertRaises(ValueError):self.run_sparse(True,'hardlink.json')
        self.assertEqual(moved.read_bytes(),self.payload)

    def test_punch_failure_keeps_readable_original_bytes_and_failure_receipt(self):
        with patch('fcntl.fcntl',side_effect=OSError('injected failure')),self.assertRaises(OSError):self.run_sparse(True)
        self.assertEqual(self.raw.read_bytes(),self.payload);self.assertIn('injected failure',json.loads((self.root/'receipt.json').read_text())['error'])

    def test_concurrent_change_after_scan_is_rejected(self):
        import portable_sparse_raw as module
        original=module.scan
        def changed(*args):
            result=original(*args)
            with self.raw.open('r+b') as f:f.write(b'Z')
            return result
        with patch.object(module,'scan',changed),patch('fcntl.fcntl') as punch,self.assertRaisesRegex(ValueError,'changed during planning'):self.run_sparse(True)
        punch.assert_not_called()


if __name__=='__main__':unittest.main()
