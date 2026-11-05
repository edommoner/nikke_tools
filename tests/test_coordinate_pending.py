"""The two pending queues stay distinct, using the original native oracle."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
spec=importlib.util.spec_from_file_location('pending_coordinate_test',ROOT/'research/verify-coordinate-pending-short.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)


class CoordinatePendingTests(unittest.TestCase):
    def test_legacy_pending_has_no_coordinate_selection_or_part_accounting(self):
        for case in suite.fixtures():
            with self.subTest(case=case['name']):
                result=suite.native_reference((case,))
                self.assertFalse(result['coordinate_selection']);self.assertFalse(result['coordinate_target_accounting'])
                self.assertTrue(all(not packet['target'] for packet in result['coordinate_packets']))

    def test_static_pack_retains_all_old_inputs_without_a_native_battle(self):
        with patch.object(suite,'native_reference',side_effect=AssertionError('No native battle in packing')):
            entries,raw=suite.prepare();old,oldraw=suite.parent.prepare()
        self.assertEqual(len(entries),60);self.assertEqual(sum(row[2] is not None for row in entries),50)
        self.assertEqual([row[:2] for row in entries[:52]],[row[:2] for row in old])
        self.assertEqual(raw[4:4+len(oldraw)-4],oldraw[4:])


if __name__=='__main__':unittest.main()
