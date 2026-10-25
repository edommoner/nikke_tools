"""Actual original stack mutations and strict ancestor source projections."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_stack_test',ROOT/'research/verify-coordinate-original-stacks-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class OriginalStackTests(unittest.TestCase):
    def test_wire_infinity_is_distinct_from_finite_display_sentinel(self):
        import struct
        from portable_specs import LIMITS as L
        block=[0]*159744;at=L['CARRIER_STATE_BASE']+5
        block[at:at+2]=[0,0x7ff00000];self.assertIsNone(a.stack_expiry(block,0))
        block[at:at+2]=struct.unpack('<II',struct.pack('<d',1e30));self.assertEqual(a.stack_expiry(block,0),1e30)

    def test_full_original_rows_and_early_kind_gate(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle in packing')):rows,_=a.prepare()
        self.assertEqual(len(rows),4);old=KindAdmission(ROOT,'gpu/world_coordinate_original_ammo_entry.slang');current=KindAdmission(ROOT,a.SOURCE)
        for _,words,domain in rows:
            case,m,_,_=domain;self.assertEqual(set(m['binding_source_indices']),set(range(len(case['effects']))))
            rejected={row['kind'] for row in old.inspect(words)['unsupported']};self.assertTrue(rejected);self.assertTrue(rejected<={16,17,19});self.assertEqual(current.inspect(words)['unsupported'],[])
            self.assertIs(provider(a,domain)[2],a.native_reference)

    def test_actual_consume_and_later_recharge_without_input_changes(self):
        row=a.fixtures()[-1];case,prepared=a.prepare_case(row);case['stack_witness']=row['stack_witness'];before=copy.deepcopy(prepared);_,m,b,d=a.compile_coordinate_battle(prepared)
        native=a.native_reference((case,m,b,d));self.assertEqual(prepared,before);self.assertTrue(a.verify_witness(case,native))
        bad=copy.deepcopy(native);bad['original_stacks']['dispatches'][-1]['after'][0]['stack']=2
        with self.assertRaises(AssertionError):a.verify_witness(case,bad)

    def test_native_methods_restore_after_failure(self):
        from calculator.buff_manager import BuffManager
        from world_original_stack_native import capture
        names=('_register_all','_dispatch_instant','_apply_buff_max_stack_add','notify');methods=[getattr(BuffManager,n) for n in names];case,_=a.prepare_case(a.fixtures()[0])
        with self.assertRaisesRegex(RuntimeError,'native failed'):
            with capture(case):raise RuntimeError('native failed')
        self.assertEqual(methods,[getattr(BuffManager,n) for n in names])

    def test_exact_source_wire_and_ancestor_inverse(self):
        from portable_coordinate_original_stack_source_contract import project_sources,project_backend_source
        from portable_coordinate_original_resource_source_contract import project_sources as ancestor
        from portable_backend import validate_composed_stride
        baseline=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-stack-source-delta.json').read_text());p=project_sources(ROOT)
        for name,row in baseline['sources'].items():self.assertEqual(p[name],row['baseline'])
        self.assertEqual(project_backend_source(ROOT),baseline['transport']['baseline']);self.assertNotIn('gpu/coordinate_vital_kind_admission.slang',ancestor(ROOT))
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_vital_kind_admission.slang':(ROOT/'gpu/coordinate_vital_kind_admission.slang').read_text()+'\n'})
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS-1)
if __name__=='__main__':unittest.main()
