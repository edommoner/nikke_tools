"""Unit-only receipts preserve mandatory native/GPU proof boundaries."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('unit_check_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
class UnitCheck(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.capture=Path(folder.name)/'capture';self.m=dict(suite='fixture',package_id='fixture')
        self.addCleanup(patch.stopall)
        patch.object(cli,'verify_package',return_value=self.m).start();patch.dict(cli.SUITES,fixture=dict(tests=['test_fixture.py'])).start()
        self.native=patch.object(cli,'cpu_preflight',side_effect=AssertionError('No full native preflight')).start()
        self.gpu=patch.object(cli,'run_job',side_effect=AssertionError('No GPU worker')).start()
    def test_successful_units_do_not_claim_full_cpu_or_gpu_calculation(self):
        with patch.object(cli,'cpu_test_groups',return_value=[dict(tests=3)]) as units:r=cli.unit_capture(self.capture)
        self.assertTrue(r['passed']);self.assertTrue(r['unit_tests_verified']);self.assertEqual((r['groups'],r['tests']),(1,3))
        for key in ('cpu_verified','full_native_preflight_executed','calculation_verified','gpu_execution_verified','full_goal_complete'):self.assertFalse(r[key])
        self.assertEqual(r['gpu_calls'],0);self.native.assert_not_called();self.gpu.assert_not_called();units.assert_called_once()
        self.assertTrue((self.capture/'artifacts.json').is_file());self.assertEqual(json.loads((self.capture/'result.json').read_text()),r)
    def test_failed_unit_gate_retains_failure_receipt_and_never_runs_native(self):
        with patch.object(cli,'cpu_test_groups',side_effect=ValueError('fixture failure')),self.assertRaisesRegex(ValueError,'fixture failure'):cli.unit_capture(self.capture)
        r=json.loads((self.capture/'result.json').read_text());self.assertFalse(r['passed']);self.assertIn('fixture failure',r['error']);self.assertTrue((self.capture/'artifacts.json').exists());self.native.assert_not_called();self.gpu.assert_not_called()
    def test_invalid_packet_stops_before_capture_or_unit_worker(self):
        with patch.object(cli,'verify_package',side_effect=ValueError('corrupt packet')),patch.object(cli,'cpu_test_groups') as units,self.assertRaisesRegex(ValueError,'corrupt packet'):cli.unit_capture(self.capture)
        units.assert_not_called();self.assertFalse(self.capture.exists())
    def test_unknown_composed_wire_stops_before_capture_or_unit_worker(self):
        with patch.dict(cli.SUITES,fixture=dict(source='gpu/unknown.slang',input_words=109536,output_words=1310720,tests=['test_fixture.py'])),patch.object(cli,'cpu_test_groups') as units,self.assertRaisesRegex(ValueError,'registered shared entry'):cli.unit_capture(self.capture)
        units.assert_not_called();self.assertFalse(self.capture.exists())
    def test_empty_registered_groups_cannot_be_a_successful_unit_check(self):
        with patch.dict(cli.SUITES,fixture=dict(tests=[])),patch.object(cli,'cpu_test_groups') as units,self.assertRaisesRegex(ValueError,'nonempty unit groups'):cli.unit_capture(self.capture)
        units.assert_not_called();self.assertFalse(self.capture.exists())
    def test_existing_capture_is_never_overwritten(self):
        self.capture.mkdir();marker=self.capture/'marker';marker.write_text('preserve')
        with patch.object(cli,'cpu_test_groups') as units,self.assertRaises(FileExistsError):cli.unit_capture(self.capture)
        units.assert_not_called();self.assertEqual(marker.read_text(),'preserve');self.assertFalse((self.capture/'result.json').exists())
    def test_parent_unit_stage_forbids_gpu_generation_as_well_as_dispatch(self):
        def units(*args,**kwargs):
            import portable_backend
            for fn,args in ((portable_backend.build,('gpu/unknown.slang','main')),(portable_backend.execute,('gpu/unknown.slang','main',b'',1,1))):
                with self.assertRaisesRegex(RuntimeError,'forbidden'):fn(*args)
            return [dict(tests=1)]
        with patch.object(cli,'cpu_test_groups',side_effect=units):self.assertTrue(cli.unit_capture(self.capture)['passed'])
        self.native.assert_not_called();self.gpu.assert_not_called()
if __name__=='__main__':unittest.main()
