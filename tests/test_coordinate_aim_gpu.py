"""Authored-only wire, retained base input, exact inverse and final-state decoder."""
import copy,importlib.util,sys,unittest,struct
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
from portable_coordinate_aim_wire import LAYOUT as A,check_schema
s=importlib.util.spec_from_file_location('aim_gpu_test_adapter',ROOT/'research/verify-coordinate-aim-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class AimGpuTests(unittest.TestCase):
    def test_all_packing_is_authored_and_base151_is_retained(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle in packing')),patch.object(a,'native_reference',side_effect=AssertionError('No oracle in packing')):
            entries,raw=a.prepare();old,_=a.parent.prepare()
        self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(190,166))
        self.assertEqual(len(raw),4+190*a.INPUT_WORDS*4)
        for before,after in zip(old,entries):
            self.assertEqual(before[0],after[0]);self.assertEqual(before[1],after[1][:A['BASE_INPUT']]);self.assertEqual(before[2],after[2])
        check_schema(ROOT)

    def test_static_controls_and_cases_are_not_erased_or_mutated(self):
        for case in a.fixtures():
            before=copy.deepcopy(case);words,meta,bindings,desc=a.compile_case(case)
            self.assertEqual(case,before)
            tail=words[A['BASE_INPUT']:]
            self.assertEqual(tail[2],('solo','warn','strict').index(case['control_mode']))
            self.assertEqual(sum(tail[8:13]),sum(len(c.get('aim',[])) for c in case['controls']))
            self.assertEqual(tail[3],len(case.get('sequence',[])))

    def test_current_source_is_strictly_projected_and_mutations_are_rejected(self):
        from portable_coordinate_aim_source_contract import project_sources
        projected=project_sources(ROOT)
        name='gpu/coordinate_physical_runtime.slang'
        self.assertNotEqual(projected[name],(ROOT/name).read_text())
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
        name='gpu/coordinate_aim_runtime.slang'
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})

    def test_new_stride_requires_full_layout(self):
        import portable_backend
        portable_backend.validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):portable_backend.validate_composed_stride(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS)

    def test_every_authored_anchor_span_survives_binary_lowering(self):
        seen=set()
        for case in a.fixtures():
            words,_,_,_=a.compile_case(case)
            for who,control in enumerate(case['controls']):
                for i,entry in enumerate(control.get('aim',[])):
                    if 'anchor' not in entry:continue
                    at=A['BASE_INPUT']+A['HEADER']+(who*8+i)*16
                    offset,length=struct.unpack('<dd',struct.pack('<IIII',*words[at+8:at+12]))
                    self.assertEqual((offset,length),(float(entry.get('offset',0)),float(entry['len'])))
                    seen.add(entry['anchor'])
        self.assertEqual(seen,{'combat_start','fb_end','own_fb_end','own_buff_end','next_fb_start'})

if __name__=='__main__':unittest.main()
