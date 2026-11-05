import engine_worker
"""Private development registration, preparation and strict transport gates."""
import importlib.util,sys,unittest
import hashlib,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from calculator import timeline
from portable_backend import validate_composed_stride

def adapter():
    spec=importlib.util.spec_from_file_location('logical_cli_test_adapter',ROOT/'research/verify-logical-actor-geometry.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class LogicalGeometryCLI(unittest.TestCase):
    pass

    def test_thirteen_inputs_retain_six_original_battles_and_raw_negatives(self):
        m=adapter()
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native battle in preparation')):rows,raw=m.prepare()
        self.assertEqual(len(rows),13);self.assertEqual(len(raw),4+13*115680*4)
        self.assertEqual(sum(domain is not None for _,_,domain in rows),6)
        self.assertEqual(len({name for name,_,_ in rows}),13)
        for name,words,domain in rows:
            self.assertEqual(len(words),115680)
            if domain is not None:self.assertEqual(domain[1]['coordinate_original_input']['prepared_definitions'],68)
            else:self.assertTrue(name.startswith('reject/logical-actor-geometry/'))

    def test_failed_readback_cannot_start_native_comparison(self):
        m=adapter()
        with patch.object(m,'native_reference',side_effect=AssertionError('Must stop before native')) as native:
            for block in ([64], [64]+[0]*(2032000-1)):
                with self.assertRaisesRegex(AssertionError,'Complete successful'):m.compare(block,None)
            native.assert_not_called()


if __name__=='__main__':unittest.main()
