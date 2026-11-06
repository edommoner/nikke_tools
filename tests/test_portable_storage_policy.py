"""Capacity policy stops new copies before allocating or executing payloads."""
import importlib.util,json,sys,tempfile,types,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_capture_storage as storage
import nikke_gpu as cli

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

    def test_unpack_low_space_leaves_destination_absent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);payload=b'ordinary source'
            row=dict(path='app/source.py',bytes=len(payload),sha256=cli.sha(payload))
            m=dict(schema=cli.SCHEMA,suite='future-suite',files=[row]);m['package_id']=cli.package_id(m)
            with zipfile.ZipFile(root/'packet.zip','w') as z:
                z.writestr('gpu-package.json',json.dumps(m));z.writestr(row['path'],payload)
            with patch.object(storage.shutil,'disk_usage',return_value=types.SimpleNamespace(free=storage.RESERVE_BYTES)):
                with self.assertRaisesRegex(ValueError,'Insufficient'):cli.unpack(root/'packet.zip',root/'destination')
            self.assertFalse((root/'destination').exists())

    def test_package_low_space_precedes_native_baseline_and_zip_creation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);upstream=root/'research/upstream/nikke-calc-master'
            (upstream/'data').mkdir(parents=True);(upstream/'data/parsed_nikke.json').write_text('{}')
            (upstream/'LICENSE').write_text('fixture')
            config=dict(tests=[],golden='research/golden.json')
            with patch.object(cli,'ROOT',root),patch.object(cli,'SUITES',dict(fixture=config)),\
                 patch.object(cli.subprocess,'check_output',return_value=b''),\
                 patch.object(cli,'file_records',return_value=[dict(path='source.py',bytes=100,sha256='x')]),\
                 patch.object(cli,'development_baseline',side_effect=AssertionError('Native work forbidden')) as native,\
                 patch.object(storage.shutil,'disk_usage',return_value=types.SimpleNamespace(free=storage.RESERVE_BYTES)):
                with self.assertRaisesRegex(ValueError,'Insufficient'):cli.make_package('fixture',root/'packet.zip',develop=True)
            native.assert_not_called();self.assertFalse((root/'packet.zip').exists())

if __name__=='__main__':unittest.main()
