"""Exact local archival must not lose raw on integrity or publication failure."""
import hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import nikke_gpu as cli
from portable_capture_storage import archive_raw,restore_raw

class CaptureStorageTests(unittest.TestCase):
    def fixture(self,root):
        capture=root/'capture';capture.mkdir();data=bytes(range(256))*513+bytes(65536)
        (capture/'readback.bin').write_bytes(data)
        cli.write(capture/'evidence.json',dict(output_sha256=hashlib.sha256(data).hexdigest(),transport=dict(output_bytes=len(data))))
        cli.write(capture/'artifacts.json',dict(files=cli.file_records(capture,['evidence.json'])))
        return capture,root/'raw.gz',data

    def test_roundtrip_keeps_exact_bytes_without_gpu_and_refuses_overwrite(self):
        import portable_backend
        with tempfile.TemporaryDirectory() as folder,patch.object(portable_backend,'build',side_effect=AssertionError('GPU forbidden')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            capture,archive,data=self.fixture(Path(folder))
            r=archive_raw(capture,archive,cli.check_records,remove_original=True)
            self.assertFalse((capture/'readback.bin').exists());self.assertLess(r['archive_bytes'],len(data));self.assertEqual(r['gpu_calls'],0)
            self.assertTrue(restore_raw(capture,archive,cli.check_records)['restored']);self.assertEqual((capture/'readback.bin').read_bytes(),data)
            with self.assertRaises(ValueError):restore_raw(capture,archive,cli.check_records)
            with self.assertRaises(ValueError):archive_raw(capture,archive,cli.check_records,remove_original=True)
            self.assertEqual((capture/'readback.bin').read_bytes(),data)

    def test_bad_source_or_verification_failure_never_removes_original(self):
        with tempfile.TemporaryDirectory() as folder:
            capture,archive,data=self.fixture(Path(folder))
            with patch('portable_capture_storage.decompress',side_effect=ValueError('roundtrip failed')):
                with self.assertRaisesRegex(ValueError,'roundtrip'):archive_raw(capture,archive,cli.check_records,remove_original=True)
            self.assertEqual((capture/'readback.bin').read_bytes(),data);self.assertFalse(archive.exists())
            (capture/'readback.bin').write_bytes(data[:-1]+b'x')
            with self.assertRaises(ValueError):archive_raw(capture,archive,cli.check_records,remove_original=True)
            self.assertTrue((capture/'readback.bin').exists());self.assertFalse(archive.exists())

    def test_corrupt_archive_or_changed_anchor_cannot_restore_partial_data(self):
        with tempfile.TemporaryDirectory() as folder:
            capture,archive,data=self.fixture(Path(folder));archive_raw(capture,archive,cli.check_records,remove_original=True)
            original=archive.read_bytes();archive.write_bytes(original[:-1]+bytes([original[-1]^1]))
            with self.assertRaises(ValueError):restore_raw(capture,archive,cli.check_records)
            self.assertFalse((capture/'readback.bin').exists());self.assertFalse(list(capture.glob('.raw-restore-*')))
            archive.write_bytes(original);(capture/'evidence.json').write_text('{}')
            with self.assertRaises(ValueError):restore_raw(capture,archive,cli.check_records)
            self.assertFalse((capture/'readback.bin').exists())

    def test_archive_must_be_outside_capture_and_requires_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            capture,archive,data=self.fixture(Path(folder))
            with self.assertRaises(ValueError):archive_raw(capture,capture/'raw.gz',cli.check_records)
            cli.write(capture/'artifacts.json',dict(files=[]))
            with self.assertRaises(ValueError):archive_raw(capture,archive,cli.check_records,remove_original=True)
            self.assertEqual((capture/'readback.bin').read_bytes(),data)
