import sys,unittest,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
from portable_coordinate_accumulation_cases import fixtures
from world_coordinate_accumulation_native import observe
from portable_coordinate_accumulation_contracts import verify

class AccumulationPolicyTests(unittest.TestCase):
    def test_observed_target_damage_is_excluded_by_the_current_native_consumer(self):
        for case in fixtures():
            native,trace=observe(case);report=verify(case,native)
            self.assertEqual(report['classification'],'native_reference_exclusion')
            self.assertFalse(report['extra_gpu_accumulation_required_for_parity'])
            self.assertFalse(report['game_rule_verified'])
            native['damage_accumulation']['final']['pools'][0]['current']+=1
            with self.assertRaises(AssertionError):verify(case,native)

    def test_actual_rewritten_cpu_keeps_accumulation_out_of_target_landings(self):
        funcs={c.co_name:c for c in timeline.simulate.__code__.co_consts if isinstance(c,types.CodeType)}
        self.assertIn('accumulate_damage',funcs['_land_boss'].co_names)
        self.assertNotIn('accumulate_damage',funcs['_land_target'].co_names)
        self.assertIn('publish_target_landing',funcs['_land_target'].co_names)

if __name__=='__main__':unittest.main()
