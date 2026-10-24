"""Coordinate packet proof boundaries and immutable static compilation."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_packet_specs import LAYOUT as P,check_schema
from portable_specs import LIMITS as L,check_schema as check_main_schema
from portable_coordinate_skill_cases import fixtures
from portable_coordinate_skill_contracts import verify
from world_coordinate_skill_native import observe
from world_frame_native import observe as physical_reference
spec=importlib.util.spec_from_file_location('coordinate_packets_test',ROOT/'research/verify-coordinate-skill-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class CoordinatePacketTests(unittest.TestCase):
    def test_arena_generated_capacity_and_static_input_without_cpu_battle(self):
        from calculator import timeline
        check_schema();check_main_schema();self.assertEqual(P['PACKET_COUNT'],L['LANDINGS']);self.assertEqual(P['CASTS'],L['DEPTH']);self.assertLessEqual(P['END'],1048576)
        case=a.fixtures()[-1];before=copy.deepcopy(case)
        with patch.object(timeline,'simulate',side_effect=AssertionError('CPU trace cannot be GPU input')):entries,packed=a.prepare();a.compile_case(case)
        self.assertEqual(case,before);self.assertEqual(len(entries),24);self.assertEqual(sum(d is not None for _,_,d in entries),19);self.assertEqual(len(packed),4+24*a.INPUT_WORDS*4)
    def test_child_selects_frame_retired_target_and_keeps_stale_accounting(self):
        case=fixtures()[-1];native,_=observe(case);self.assertTrue(verify(case,native)['verified'])
        self.assertEqual([s['retired_targets'] for s in native['coordinate_skill']['selections']],[[],['near']]);self.assertEqual(native['damage'][0],8800)
        self.assertEqual([x['pool_hits_delta'] for x in native['coordinate_skill']['target_accounting']],[1,1,0,0])
    def test_part_threshold_child_refresh_completes_before_death_and_stale_packet(self):
        case=a.fixtures()[-1];result=a.native_reference((case,));rows=result['battle']['target_counters']['completions'];self.assertEqual([r['reason'] for r in rows],['threshold','death']);self.assertEqual([r['epoch'] for r in rows],[1,2]);self.assertEqual(result['battle']['damage'][0],16000)
    def test_physical_negative_really_contains_native_coordinate_shots(self):
        case=copy.deepcopy(a.fixtures()[0]);case['combat']['weapons'][0].update(charge=.05,min_cycle=.05,interval=.05)
        native=physical_reference(case);self.assertGreater(native['shots'][0],0)
if __name__=='__main__':unittest.main()
