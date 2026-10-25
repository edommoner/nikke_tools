"""Control/mode compositions retain old wire and execute actual native producers."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
s=importlib.util.spec_from_file_location('control_adapter',ROOT/'research/verify-coordinate-control-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ControlTests(unittest.TestCase):
    def test_every_composition_reaches_real_native_battle_and_control_contract(self):
        cases=a.fixtures();self.assertEqual(len(cases),16)
        for c in cases:
            before=copy.deepcopy(c);w,m,b,d=a.compile_case(c);v=a.native_reference((c,m,b,d))
            self.assertEqual(c,before);self.assertTrue(v['physical_pellets']);self.assertTrue(v['coordinate_aim']['frames'])
    def test_packing_is_oracle_free_and_retains_all190_entries(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native schedule in wire')),patch.object(a,'native_reference',side_effect=AssertionError('No oracle in wire')):
            new,raw=a.prepare();old,_=a.parent.prepare()
        self.assertEqual(new[:190],old)
        self.assertEqual((len(new),sum(d is not None for _,_,d in new)),(206,182))
        self.assertEqual(len(raw),4+206*a.INPUT_WORDS*4)
    def test_exact_inverse_rejects_any_unreviewed_runtime_or_entry(self):
        from portable_coordinate_control_source_contract import project_sources
        self.assertIn('gpu/coordinate_aim_runtime.slang',project_sources(ROOT))
        for name in ['gpu/coordinate_aim_runtime.slang','gpu/world_coordinate_control_entry.slang']:
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
    def test_composed_entry_keeps_the_complete_aim_wire(self):
        import portable_backend
        portable_backend.validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):portable_backend.validate_composed_stride(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS)
    def test_group_frontier_reports_real_conflicts_without_enabling_or_shrinking(self):
        from portable_coordinate_group_frontier import verify
        with patch.object(timeline,'simulate',side_effect=AssertionError('Static only')):result=verify(ROOT)
        self.assertFalse(result['current']['address_plan_verified'])
        self.assertTrue(result['proposal']['address_plan_verified'])
        self.assertTrue(result['proposed_addresses_implemented'])
        self.assertTrue(result['physical_group_receipts_connected'])
        self.assertTrue(result['add_sharing_connected'])
        self.assertEqual(result['gpu_calls'],0)

if __name__=='__main__':unittest.main()
