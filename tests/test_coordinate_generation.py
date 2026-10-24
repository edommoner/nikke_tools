"""Native landing generations differ from frozen coordinate selections."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from calculator import timeline
from calculator.boss_pattern import BossScript
spec=importlib.util.spec_from_file_location('coordinate_generation_test',ROOT/'research/verify-coordinate-generation-short.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)


class CoordinateGenerationTests(unittest.TestCase):
    def test_native_name_resolution_retirement_counters_and_mixed_generations(self):
        for case in suite.fixtures():
            with self.subTest(case=case['name']):suite.native_reference((case,))

    def test_static_input_retains_all76_and_never_packs_a_landing_generation(self):
        with patch.object(suite,'native_reference',side_effect=AssertionError('No native battle in input')),patch.object(timeline,'simulate',side_effect=AssertionError('No simulation in input')),patch.object(BossScript,'hit_target',side_effect=AssertionError('No CPU landing in input')):
            entries,raw=suite.prepare();old,oldraw=suite.parent.prepare()
        self.assertEqual(len(entries),88);self.assertEqual(sum(row[2] is not None for row in entries),75)
        self.assertEqual([row[:2] for row in entries[:76]],[row[:2] for row in old])
        self.assertEqual(raw[4:len(oldraw)],oldraw[4:])


if __name__=='__main__':unittest.main()
