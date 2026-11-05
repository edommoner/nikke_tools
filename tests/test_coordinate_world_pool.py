"""Native transparency, live pool order and static-only shared pool input."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_pool_cases import fixtures
from world_coordinate_pool_native import observe
from world_parts_skill_native import observe as original_observe
spec=importlib.util.spec_from_file_location('world_coordinate_pool_test',ROOT/'research/verify-coordinate-world-pool-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class CoordinatePoolTests(unittest.TestCase):
    def test_projection_preserves_actual_native_battle_and_input(self):
        case=fixtures()[3];before=copy.deepcopy(case);native,trace=original_observe(case);native.pop('parts_skill_events');native.pop('parts_skill_accounting')
        result=observe(case);self.assertEqual(result['battle'],native);self.assertEqual(result['skill_trace'],trace);self.assertEqual(case,before)
    def test_canonical_live_pool_depth_and_body_exclusion(self):
        cases=fixtures();a0=observe(cases[6])['coordinate_pool'];a1=observe(cases[7])['coordinate_pool']
        self.assertEqual([r[0] for r in a0['all']],[3,1,2]);self.assertEqual([r[0] for r in a1['all']],[2,3,1]);self.assertEqual([r[0] for r in a1['parts']],[2,1]);self.assertEqual(observe(cases[5])['coordinate_pool']['all'],[])
    def test_reopened_generation_birth_and_ordinal_read_from_real_pool(self):
        cases={c['name']:c for c in fixtures()}
        snapshot=observe(cases['coordinate-pool/reopen-live'])['coordinate_pool'];self.assertEqual([r[3] for r in snapshot['all']],[2,2])
        snapshot=observe(cases['coordinate-pool/later-birth'])['coordinate_pool'];self.assertEqual([r[0] for r in snapshot['all']],[2,1,3])
        snapshot=observe(cases['coordinate-pool/same-pattern-ordinal'])['coordinate_pool'];self.assertEqual([r[0] for r in snapshot['all']],[2,1])
    def test_pack_never_executes_battle_and_snapshot_covers_reserved_region(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle input')):entries,data=a.prepare()
        self.assertEqual(len(entries),16);self.assertEqual(len(data),4+16*a.INPUT_WORDS*4)
        snapshot=observe(entries[0][2][0])['coordinate_pool'];out=a.expected_snapshot(snapshot);self.assertEqual(len(out),a.OUTPUT_WORDS-a.BASE_OUTPUT);self.assertEqual(out[-1],0)
if __name__=='__main__':unittest.main()
