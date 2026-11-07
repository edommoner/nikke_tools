"""Capacity policy stops new copies before allocating or executing payloads."""
import sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_capture_storage as storage

class StoragePolicyTests(unittest.TestCase):
    def test_twenty_gib_default_exact_boundary_and_explicit_override(self):
        self.assertEqual(storage.RESERVE_BYTES,20*1024**3)
        with patch.object(storage.shutil,'disk_usage',return_value=types.SimpleNamespace(free=storage.RESERVE_BYTES-1)):
            self.assertFalse(storage.space_status(ROOT)['passed'])
            with self.assertRaises(ValueError):storage.require_space(ROOT,0)
            self.assertTrue(storage.space_status(ROOT,reserve=0)['passed'])
        with patch.object(storage.shutil,'disk_usage',return_value=types.SimpleNamespace(free=storage.RESERVE_BYTES+100)):
            self.assertTrue(storage.space_status(ROOT,100)['passed'])
            self.assertFalse(storage.space_status(ROOT,101)['passed'])

    def test_bundle_and_restore_budget_before_allocating(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/'raw';src.write_bytes(b'fixture')
            anchor=dict(size=7,sha256=hashlib.sha256(b'fixture').hexdigest())
            with patch.object(storage.shutil,'disk_usage',return_value=types.SimpleNamespace(free=storage.RESERVE_BYTES)):
                with self.assertRaisesRegex(ValueError,'Insufficient'):storage.archive_bundle(src,root/'bundle',anchor)
            self.assertFalse((root/'bundle').exists());self.assertEqual(src.read_bytes(),b'fixture')
            storage.archive_bundle(src,root/'bundle',anchor)
            with patch.object(storage.shutil,'disk_usage',return_value=types.SimpleNamespace(free=storage.RESERVE_BYTES)):
                with self.assertRaisesRegex(ValueError,'Insufficient'):storage.restore_bundle(root/'bundle',anchor,root/'restored')
            self.assertFalse((root/'restored').exists())

if __name__=='__main__':unittest.main()
