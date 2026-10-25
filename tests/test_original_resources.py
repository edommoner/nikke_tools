"""Complete original gauge effects and actual cap-dependent callback behavior."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_resource_test',ROOT/'research/verify-coordinate-original-resources-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class OriginalResourceTests(unittest.TestCase):
    def test_complete_inputs_pack_without_cpu_battle(self):
        from calculator import timeline
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in input')):rows,_=a.prepare()
        self.assertEqual(len(rows),3)
        for _,words,domain in rows:
            c,m,_,_=domain
            self.assertIn(len(c['effects']),(76,83));self.assertEqual(set(m['binding_source_indices']),set(range(len(c['effects']))))
            self.assertEqual(len(words),a.INPUT_WORDS);self.assertIs(provider(a,domain)[2],a.native_reference)

    def test_cap_and_later_callbacks_are_actual_original_execution(self):
        row=a.fixtures()[1];c,p=a.prepare_case(row);c['resource_witness']=row['resource_witness'];before=copy.deepcopy(p);_,m,b,d=a.compile_coordinate_battle(p)
        previous=sys.getprofile();native=a.native_reference((c,m,b,d));self.assertIs(sys.getprofile(),previous);self.assertEqual(p,before)
        self.assertTrue(a.verify_witness(c,native))
        wrong=copy.deepcopy(native);wrong['original_resources']['final']['E.H.']['사제 탄창']=3
        with self.assertRaises(AssertionError):a.verify_witness(c,wrong)

    def test_observer_restores_original_methods_on_failure(self):
        from calculator.buff_manager import BuffManager
        from world_original_resource_native import capture
        methods=[getattr(BuffManager,n) for n in ('_register_all','_dispatch_instant','notify')]
        c,_=a.prepare_case(a.fixtures()[0])
        with self.assertRaisesRegex(RuntimeError,'native failure'):
            with capture(c):raise RuntimeError('native failure')
        self.assertEqual(methods,[getattr(BuffManager,n) for n in ('_register_all','_dispatch_instant','notify')])
if __name__=='__main__':unittest.main()
