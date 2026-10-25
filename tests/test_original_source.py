"""Original slot forcing and real DoT continuation after the old deadline."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_source_test',ROOT/'research/verify-coordinate-original-source-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class OriginalSourceTests(unittest.TestCase):
    def test_complete_original_inputs_and_early_kind_rejection(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in input')):rows,_=a.prepare()
        self.assertEqual(len(rows),5);old=KindAdmission(ROOT,'gpu/world_coordinate_original_cleanse_entry.slang');current=KindAdmission(ROOT,a.SOURCE)
        for _,words,domain in rows:
            c,m,_,_=domain;self.assertEqual(set(m['binding_source_indices']),set(range(len(c['effects']))))
            kinds={r['kind'] for r in old.inspect(words)['unsupported']};self.assertIn(33,kinds);self.assertTrue(kinds<={15,33});self.assertEqual(current.inspect(words)['unsupported'],[])
            self.assertIs(provider(a,domain)[2],a.native_reference)

    def test_actual_part_destruction_extends_real_damage_beyond_old_expiry(self):
        row=a.fixtures()[-1];c,p=a.prepare_case(row);c['source_witness']=row['source_witness'];before=copy.deepcopy(p);_,m,b,d=a.compile_coordinate_battle(p)
        native=a.native_reference((c,m,b,d));self.assertEqual(before,p);self.assertTrue(a.verify_witness(c,native))
        bad=copy.deepcopy(native);events=bad['original_source']['dispatches'];events[-1]['after'][1]['dot']['next']+=1
        with self.assertRaises(AssertionError):a.verify_witness(c,bad)

    def test_observer_restores_methods_on_failure(self):
        from calculator.buff_manager import BuffManager
        from world_original_source_native import capture
        names=('_register_all','_dispatch_instant','_activate');before=[getattr(BuffManager,n) for n in names];c,_=a.prepare_case(a.fixtures()[0])
        with self.assertRaisesRegex(RuntimeError,'native failed'):
            with capture(c):raise RuntimeError('native failed')
        self.assertEqual(before,[getattr(BuffManager,n) for n in names])

    def test_exact_source_and_transport_inverse(self):
        from portable_coordinate_original_slot_source_contract import project_sources,project_backend_source
        from portable_coordinate_original_resource_source_contract import project_sources as ancestor
        from portable_backend import validate_composed_stride
        baseline=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-slot-source-delta.json').read_text());p=project_sources(ROOT)
        for name,row in baseline['sources'].items():self.assertEqual(p[name],row['baseline'])
        self.assertEqual(project_backend_source(ROOT),baseline['transport']['baseline']);self.assertNotIn('gpu/coordinate_vital_kind_admission.slang',ancestor(ROOT))
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_vital_kind_admission.slang':(ROOT/'gpu/coordinate_vital_kind_admission.slang').read_text()+'\n'})
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS-1)
if __name__=='__main__':unittest.main()
