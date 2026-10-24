"""Original coordinate selection and pending order contracts, both backends."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
spec=importlib.util.spec_from_file_location('coordinate_full_burst_test',ROOT/'research/verify-coordinate-full-burst-short.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)


class CoordinateFullBurstTests(unittest.TestCase):
    def test_original_pending_shapes_reference_counts_and_receipt_tails(self):
        for case in suite.fixtures():
            with self.subTest(case=case['name']):suite.native_reference((case,))

    def test_retained60_inputs_and_new_descriptor_guards_without_native_execution(self):
        with patch.object(suite,'native_reference',side_effect=AssertionError('No native battle in input')):
            entries,raw=suite.prepare();old,oldraw=suite.parent.prepare()
        self.assertEqual(len(entries),76);self.assertEqual(sum(row[2] is not None for row in entries),63)
        self.assertEqual([row[:2] for row in entries[:60]],[row[:2] for row in old])
        self.assertEqual(raw[4:len(oldraw)],oldraw[4:])


if __name__=='__main__':unittest.main()
