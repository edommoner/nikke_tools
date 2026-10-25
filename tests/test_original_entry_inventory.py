"""Static packing is auditable without admitting or executing a GPU battle."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research'),str(ROOT/'scripts')]
import engine_worker
import portable_original_entry_inventory as inventory
from nikke_gpu import write,forbid_gpu
class EntryInventoryTests(unittest.TestCase):
    def test_full_inventory_separates_packing_from_gpu_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.json';result=inventory.run(path,write=write,forbid_gpu=forbid_gpu);report=json.loads(path.read_text())
        self.assertTrue(result['passed']);self.assertEqual(result['profile_count'],266);self.assertEqual(result['packed_profiles'],247)
        self.assertEqual(result['forbidden_calls'],dict(cpu_battle=0,gpu=0))
        self.assertFalse(result['gpu_admission_verified']);self.assertFalse(result['calculation_verified'])
        gauge_profiles=report['definition_kind_profiles']['9']
        self.assertEqual(len(gauge_profiles),15)
        self.assertTrue(all(not row['gpu_admission_verified'] for row in report['profiles']))

    def test_battle_attempt_preserves_failed_report_and_refuses_overwrite(self):
        from calculator import timeline
        from portable_coordinate_original_revival_cases import fixtures
        from portable_coordinate_original_cases import prepare_case
        _,prepared=prepare_case(fixtures()[0])
        def bad(*args):return timeline.simulate([])
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'failed.json'
            with patch.object(inventory,'prepared_profiles',return_value=iter([('마나',0,prepared)])),patch('portable_coordinate_roster_input.compile_coordinate_battle',bad):
                with self.assertRaisesRegex(AssertionError,'forbids cpu_battle'):inventory.run(output,write=write,forbid_gpu=forbid_gpu)
            report=json.loads(output.read_text());self.assertFalse(report['passed']);self.assertEqual(report['forbidden_calls']['cpu_battle'],1)
            before=output.read_bytes()
            with self.assertRaises(FileExistsError):inventory.run(output,write=write,forbid_gpu=forbid_gpu)
            self.assertEqual(output.read_bytes(),before)

    def test_shared_identity_catalog_remains_nonpacking(self):
        from portable_original_identity_inventory import inspect
        import portable_runtime
        with patch.object(portable_runtime,'compile_program',side_effect=AssertionError('Identity catalog cannot pack')):result=inspect()
        self.assertEqual(result['profiles'],266);self.assertEqual(result['nonperiodic_duplicate_groups'],[])
if __name__=='__main__':unittest.main()
