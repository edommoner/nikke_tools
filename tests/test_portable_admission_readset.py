import concurrent.futures,hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_admission_readset as trace
import portable_admission_snapshot as snap
import portable_capture_storage as storage


class ReadSetTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        self.p=self.root/'source';self.p.write_bytes('日本語\r\nline\rnext\n'.encode())
    def test_text_semantics_and_streaming_digest_match_uninstrumented_readers(self):
        expected=self.p.read_text();raw=self.p.read_bytes();digest=storage.file_digest(self.p)
        with trace.ReadSet() as reads:
            self.assertEqual(self.p.read_text(),expected)
            self.assertEqual(self.p.read_text('utf-8','strict'),expected)
            self.assertEqual(self.p.read_bytes(),raw)
            self.assertEqual(storage.file_digest(self.p),digest)
        self.assertEqual(reads.rows(),[dict(root=str(self.root),path='source',bytes=len(raw),sha256=digest)])
        with self.assertRaises(TypeError):
            with trace.ReadSet():self.p.read_text(unknown=True)
        with trace.ReadSet():self.assertEqual(self.p.read_text(),expected)
    def test_encoding_errors_and_newline_behavior(self):
        self.p.write_bytes(b'\xff\r\n')
        expected=self.p.read_text(encoding='utf-8',errors='replace')
        with trace.ReadSet():
            self.assertEqual(self.p.read_text(encoding='utf-8',errors='replace'),expected)
            with self.assertRaises(UnicodeDecodeError):self.p.read_text(encoding='utf-8')
    def test_changed_repeat_read_rejected_and_hooks_restored_on_failure(self):
        original=Path.read_bytes
        with self.assertRaisesRegex(ValueError,'between reads'):
            with trace.ReadSet():
                self.p.read_bytes();self.p.write_bytes(b'changed');self.p.read_bytes()
        self.assertIs(Path.read_bytes,original)
    def test_parallel_reads_and_nested_capture(self):
        with trace.ReadSet() as reads:
            with self.assertRaises(RuntimeError):
                with trace.ReadSet():pass
            with concurrent.futures.ThreadPoolExecutor(4) as pool:
                values=list(pool.map(storage.file_digest,[self.p]*32))
        self.assertEqual(len(set(values)),1);self.assertEqual(len(reads.rows()),1)
    def test_complete_closure_and_snapshot_recheck(self):
        row=dict(path='source',bytes=self.p.stat().st_size,sha256=storage.file_digest(self.p))
        with trace.ReadSet() as reads:storage.file_digest(self.p)
        reads.require_package(self.root,{'files':[row]})
        wrong=dict(row,sha256='0'*64)
        with self.assertRaises(ValueError):reads.require_package(self.root,{'files':[wrong]})
        with self.assertRaises(ValueError):reads.require_package(self.root,{'files':[dict(row,path='absent')]})
        binding=dict(owner_package_id='a'*64,controller_package_id='b'*64,transaction_nonce='c'*32,input_sha256=row['sha256'],artifact_sha256='d'*64,future_capture=str(self.root/'future'))
        inventory=dict(schema=snap.INVENTORY,binding=binding,files=reads.rows())
        other=tempfile.TemporaryDirectory();self.addCleanup(other.cleanup)
        out=Path(other.name)/'snapshot.zip'
        result=snap.freeze(inventory,out)
        self.assertFalse(result['admission_verified'])
        self.p.write_bytes(b'x'*row['bytes'])
        with self.assertRaisesRegex(ValueError,'bytes changed'):snap.freeze(inventory,out.parent/'changed.zip')
    def test_single_use_prevents_carrying_rows_into_another_audit(self):
        reads=trace.ReadSet()
        with reads:self.p.read_bytes()
        with self.assertRaises(RuntimeError):
            with reads:pass
        with trace.ReadSet():self.p.read_bytes()
    def test_streaming_digest_mutation_is_rejected(self):
        from unittest.mock import patch
        original=storage.file_digest
        def mutate(path):
            result=original(path);Path(path).write_bytes(b'mutation');return result
        with patch.object(storage,'file_digest',mutate):
            with self.assertRaisesRegex(ValueError,'during digest'):
                with trace.ReadSet():storage.file_digest(self.p)
    def test_trace_is_not_claimed_to_cover_arbitrary_open(self):
        with trace.ReadSet() as reads:
            with self.p.open('rb') as f:f.read()
        self.assertEqual(reads.rows(),[])
        with self.assertRaisesRegex(ValueError,'Incomplete'):reads.require_package(self.root,{'files':[dict(path='source',bytes=self.p.stat().st_size,sha256=storage.file_digest(self.p))]})


if __name__=='__main__':unittest.main()
