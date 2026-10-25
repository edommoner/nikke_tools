"""Original selective cleanse retains unselected recipients and immutable input."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_cleanse_test',ROOT/'research/verify-coordinate-original-cleanse-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class OriginalCleanseTests(unittest.TestCase):
    def test_shared_world_node_reader_preserves_dispel_fields(self):
        import struct
        from portable_specs import LIMITS as L
        from world_overlay_node_readback import read_nodes
        at=L['WORLD_OVERLAY_STATE_BASE']+32;block=[0]*(at+8)
        block[at]=2;block[at+1]=1;block[at+4:at+6]=struct.unpack('<II',struct.pack('<d',3.5));block[at+6]=4
        self.assertEqual(read_nodes(block,1),[dict(blocked=3.5,opens=2)])
        self.assertEqual(read_nodes(block,1,cleanse=True),[dict(blocked=3.5,opens=2,dispelled=True,dispels=4)])
        block[at+1]=2
        with self.assertRaises(ValueError):read_nodes(block,1,cleanse=True)

    def test_complete_definitions_and_early_shared_kind_gate(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('CPU battle forbidden in packing')):rows,_=a.prepare()
        self.assertEqual(len(rows),4);old=KindAdmission(ROOT,'gpu/world_coordinate_original_stack_entry.slang');current=KindAdmission(ROOT,a.SOURCE)
        for _,words,domain in rows:
            c,m,_,_=domain;self.assertEqual(set(m['binding_source_indices']),set(range(len(c['effects']))))
            self.assertEqual({r['kind'] for r in old.inspect(words)['unsupported']},{26});self.assertEqual(current.inspect(words)['unsupported'],[])
            self.assertIs(provider(a,domain)[2],a.native_reference)

    def test_real_random_cleanse_keeps_three_original_recipients(self):
        row=a.fixtures()[1];c,p=a.prepare_case(row);c.update(cleanse_witness=row['cleanse_witness'],observe_overlay=True,observe_cleanse=True);before=copy.deepcopy(p);_,m,b,d=a.compile_coordinate_battle(p)
        native=a.native_reference((c,m,b,d));self.assertEqual(before,p);self.assertTrue(a.verify_witness(c,native))
        bad=copy.deepcopy(native);bad['original_cleanse']['dispatches'][-1]['after'][0]['members'].pop()
        with self.assertRaises(AssertionError):a.verify_witness(c,bad)

    def test_observer_restores_original_methods_on_exception(self):
        from calculator.buff_manager import BuffManager
        from world_original_cleanse_native import capture
        methods=[BuffManager._register_all,BuffManager._dispatch_instant];c,_=a.prepare_case(a.fixtures()[0])
        with self.assertRaisesRegex(RuntimeError,'native failed'):
            with capture(c):raise RuntimeError('native failed')
        self.assertEqual(methods,[BuffManager._register_all,BuffManager._dispatch_instant])

    def test_source_inverse_and_wire_are_exact(self):
        from portable_coordinate_original_cleanse_source_contract import project_sources,project_backend_source
        from portable_coordinate_original_resource_source_contract import project_sources as ancestor
        from portable_backend import validate_composed_stride
        baseline=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-cleanse-source-delta.json').read_text());p=project_sources(ROOT)
        for name,row in baseline['sources'].items():self.assertEqual(p[name],row['baseline'])
        self.assertEqual(project_backend_source(ROOT),baseline['transport']['baseline']);self.assertNotIn('gpu/coordinate_vital_kind_admission.slang',ancestor(ROOT))
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_vital_kind_admission.slang':(ROOT/'gpu/coordinate_vital_kind_admission.slang').read_text()+'\n'})
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS)
if __name__=='__main__':unittest.main()
