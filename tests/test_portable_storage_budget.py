"""Low storage must stop before a GPU claim, not shrink a workload."""
import json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import nikke_gpu as cli
from portable_capture_storage import space_status

class StorageBudgetTests(unittest.TestCase):
    def test_exact_boundary_and_invalid_budgets(self):
        with tempfile.TemporaryDirectory() as folder,patch('portable_capture_storage.shutil.disk_usage',return_value=types.SimpleNamespace(free=110)):
            self.assertTrue(space_status(Path(folder)/'new'/'capture',100,reserve=10)['passed'])
            self.assertFalse(space_status(folder,101,reserve=10)['passed'])
            for needed,reserve in [(True,0),(-1,0),(1,-1),(1,1.)]:
                with self.assertRaises(ValueError):space_status(folder,needed,reserve=reserve)
    def manifest(self):return dict(suite='destructible-original-battle',golden=dict(entries=[{}]*8))
    def test_both_payloads_budgeted_then_only_remaining_readback(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);adapter=types.SimpleNamespace(suite=types.SimpleNamespace(INPUT=16))
            with patch.object(cli,'open_suite',return_value=adapter),patch('portable_capture_storage.shutil.disk_usage',return_value=types.SimpleNamespace(free=2**40)):
                report=cli.capture_storage_preflight(self.manifest(),path)
                self.assertEqual(report['required_bytes'],516+8*1048576*4)
                (path/'input.bin').write_bytes(bytes(516));second=cli.capture_storage_preflight(self.manifest(),path,prepared=True)
                self.assertEqual(second['required_bytes'],8*1048576*4);self.assertFalse(second['calculation_verified']);self.assertEqual(second['gpu_calls'],0)
    def test_insufficient_storage_preserves_diagnostic_and_consumes_no_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            with patch.object(cli,'open_suite',return_value=types.SimpleNamespace(suite=types.SimpleNamespace(INPUT=16))),patch('portable_capture_storage.shutil.disk_usage',return_value=types.SimpleNamespace(free=1)):
                with self.assertRaisesRegex(ValueError,'Insufficient space'):cli.capture_storage_preflight(self.manifest(),path)
            self.assertEqual(sorted(p.name for p in path.iterdir()),['storage.json']);self.assertFalse(json.loads((path/'storage.json').read_text())['passed'])
    def test_cli_low_storage_is_exit2_with_no_gpu_or_cleanup(self):
        with patch('portable_capture_storage.shutil.disk_usage',return_value=types.SimpleNamespace(free=10)),patch('builtins.print'):
            with self.assertRaises(SystemExit) as error:cli.main(['storage-check','--required-bytes','11','--reserve-bytes','0'])
        self.assertEqual(error.exception.code,2)
    def test_wrong_prepared_size_cannot_reduce_the_budget(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(cli,'open_suite',return_value=types.SimpleNamespace(suite=types.SimpleNamespace(INPUT=16))):
            path=Path(folder);(path/'input.bin').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'size differs'):cli.capture_storage_preflight(self.manifest(),path,prepared=True)

    def test_replay_budgets_full_logical_copies_and_rejects_before_allocation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';source.mkdir();dest=root/'dest';dest.mkdir()
            names=('input.bin','readback.bin','evidence.json','generated.cu','generated.metal','execution.json')
            for name in names:(source/name).write_bytes(b'bytes')
            with patch('portable_capture_storage.shutil.disk_usage',return_value=types.SimpleNamespace(free=2**40)):
                result=cli.replay_storage_preflight(dest,source);self.assertEqual(result['required_bytes'],30)
            with patch('portable_capture_storage.shutil.disk_usage',return_value=types.SimpleNamespace(free=1)):
                with self.assertRaisesRegex(ValueError,'Insufficient space'):cli.replay_storage_preflight(dest,source)
            self.assertFalse((dest/'readback.bin').exists());self.assertFalse(cli.load(dest/'storage.json')['passed'])
    def test_replay_route_stops_with_failure_receipt_before_copy_or_compare(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';source.mkdir();dest=root/'dest'
            for name in ('input.bin','readback.bin','evidence.json','generated.cu','generated.metal','execution.json'):(source/name).write_bytes(b'bytes')
            with patch.object(cli,'verify_package',return_value=dict(package_id='new')),patch.object(cli,'replay_source',return_value=({}, {}, {})),patch('portable_capture_storage.shutil.disk_usage',return_value=types.SimpleNamespace(free=1)),patch.object(cli,'audit_replay_capture') as compare:
                with self.assertRaisesRegex(ValueError,'Insufficient space'):cli.replay_capture(dest,root/'package',source)
            compare.assert_not_called();self.assertEqual(cli.load(dest/'run.json')['status'],'failed');self.assertTrue((dest/'artifacts.json').is_file());self.assertFalse((dest/'readback.bin').exists());self.assertEqual((source/'readback.bin').read_bytes(),b'bytes')
if __name__=='__main__':unittest.main()
