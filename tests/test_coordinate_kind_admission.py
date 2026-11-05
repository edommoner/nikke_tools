"""The emitted guard and native/GPU early gate share one declaration."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research'),str(ROOT/'scripts')]
from portable_coordinate_kind_admission import KindAdmission,render,FRAGMENT

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


    def test_runtime_burst_control_predicate_is_not_assumed(self):
        from portable_burst_control_specs import INPUT_BASE
        words=list(self.rows[0][1]);words[INPUT_BASE+2]=0
        unsupported=KindAdmission(ROOT,self.a.SOURCE).inspect(words)['unsupported']
        self.assertIn(5,{r['kind'] for r in unsupported})

    def test_current_wire_and_layout(self):
        import json
        from portable_backend import validate_composed_stride
        validate_composed_stride(self.a.SOURCE, self.a.INPUT_WORDS, self.a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):
            validate_composed_stride(self.a.SOURCE, self.a.INPUT_WORDS - 1, self.a.OUTPUT_WORDS)
if __name__=='__main__':unittest.main()
