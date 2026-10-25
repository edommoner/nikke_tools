"""The emitted guard and native/GPU early gate share one declaration."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research'),str(ROOT/'scripts')]
from portable_coordinate_kind_admission import KindAdmission,render,FRAGMENT
import nikke_gpu

def adapter():
    spec=importlib.util.spec_from_file_location('resource_kind_test',ROOT/'research/verify-coordinate-original-resources-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);return a
class KindAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.a=adapter();cls.rows,_=cls.a.prepare()
    def test_guard_is_generated_and_actual_original_gauges_are_distinguished(self):
        self.assertEqual((ROOT/FRAGMENT).read_text(),render())
        _,words,_=self.rows[0]
        old=KindAdmission(ROOT,'gpu/world_coordinate_original_entry.slang').inspect(words)
        self.assertEqual({r['kind'] for r in old['unsupported']},{9,10})
        new=KindAdmission(ROOT,self.a.SOURCE).inspect(words)
        self.assertTrue(new['checked']);self.assertFalse(new['gpu_admission_verified']);self.assertEqual(new['unsupported'],[])
        with patch('portable_coordinate_kind_admission.render',return_value=render()+'\n'):
            with self.assertRaisesRegex(ValueError,'declared policy'):KindAdmission(ROOT,self.a.SOURCE)

    def test_historical_centi_status64_is_now_detectable_without_gpu(self):
        from portable_coordinate_original_burst_revival_cases import fixtures
        from portable_coordinate_original_cases import prepare_case
        _,prepared=prepare_case(fixtures()[-1]);words,_,_,_=self.a.compile_coordinate_battle(prepared)
        old=KindAdmission(ROOT,'gpu/world_coordinate_original_entry.slang').inspect(words)
        self.assertEqual({r['kind'] for r in old['unsupported']},{22})
        clock=KindAdmission(ROOT,'gpu/world_coordinate_original_clock_entry.slang').inspect(words)
        self.assertEqual(clock['unsupported'],[])

    def test_development_rejects_before_any_native_or_gpu_execution(self):
        fake=SimpleNamespace(prepare=lambda:(self.rows,None))
        native=Mock(side_effect=AssertionError('Native must not start'))
        with patch.object(nikke_gpu,'open_suite',return_value=fake),patch.object(nikke_gpu,'native_hash',native):
            with self.assertRaisesRegex(ValueError,'rejected before native/GPU'):nikke_gpu.development_baseline('coordinate-original',[])
        native.assert_not_called()

    def test_explicit_subset_and_expected_rejections_remain_valid(self):
        from portable_coordinate_original_cases import prepare_case
        from portable_coordinate_original_revival_cases import fixtures
        case,prepared=prepare_case(fixtures()[0]);words,m,b,d=self.a.compile_coordinate_battle(prepared)
        entries=[self.rows[0],('good',words,(case,m,b,d)),('expected-rejection',self.rows[0][1],None)]
        fake=SimpleNamespace(prepare=lambda:(entries,None))
        selected,_=nikke_gpu.prepare_entries(fake,dict(suite='coordinate-original',purpose='development',selected_cases=['good']))
        self.assertEqual([r[0] for r in selected],['good'])
        selected,_=nikke_gpu.prepare_entries(fake,dict(suite='coordinate-original',purpose='development',selected_cases=['expected-rejection']))
        self.assertIsNone(selected[0][2])

    def test_runtime_burst_control_predicate_is_not_assumed(self):
        from portable_burst_control_specs import INPUT_BASE
        words=list(self.rows[0][1]);words[INPUT_BASE+2]=0
        unsupported=KindAdmission(ROOT,self.a.SOURCE).inspect(words)['unsupported']
        self.assertIn(5,{r['kind'] for r in unsupported})

    def test_source_inverse_and_wire_reject_unreviewed_changes(self):
        import json
        from portable_coordinate_original_resource_source_contract import project_sources,project_backend_source
        from portable_backend import validate_composed_stride
        baseline=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-resource-source-delta.json').read_text())
        projected=project_sources(ROOT)
        for name,row in baseline['sources'].items():self.assertEqual(projected[name],row['baseline'])
        self.assertEqual(project_backend_source(ROOT),baseline['transport']['baseline'])
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_sampling_runtime.slang':(ROOT/'gpu/coordinate_sampling_runtime.slang').read_text()+'\n'})
        validate_composed_stride(self.a.SOURCE,self.a.INPUT_WORDS,self.a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(self.a.SOURCE,self.a.INPUT_WORDS-1,self.a.OUTPUT_WORDS)
if __name__=='__main__':unittest.main()
