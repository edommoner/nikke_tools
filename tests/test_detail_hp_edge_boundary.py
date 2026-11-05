"""Pre-CUDA validation for HP events and their private continuation frames."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_bounds',ROOT/'scripts/verify-hp-edge.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
g=v.g
class HPEdgeBoundaries(unittest.TestCase):
    def setUp(self):
        b=v.s.v.body(1);b['enemy']['patterns']=[]
        with v.s.v.context('controlled',{v.N[0]:[v.B('fractional crossing','atk_pct',10,event='hp_below:60.125')]}):
            self.compiled=v.s.v.v.a.evaluate({**b,'_compile_detail':True})
    def test_fractional_threshold_keeps_distinct_HP_event_code(self):
        d=self.compiled['program']['effects'][0][g.TD:g.TD+g.TS]
        self.assertEqual((d[0],d[4],d[6]),(48,60.125,-11))
    def test_nonfinite_and_invalid_counted_timings_fail_compilation(self):
        chars=self.compiled['program']['chars']
        for timing in ('hp_below:nan','hp_below:inf','event:ally_hp_below:-inf','hp_below_count:60:0','hp_below_count:60:-1','hp_below_count:60:1:2','event:adjacent_hp_below:60:oops'):
            with self.subTest(timing=timing),self.assertRaises(g.UnsupportedDetail):g.compile_effects(chars,[(v.B('invalid','atk_pct',1,event=timing),v.N[0])])
if __name__=='__main__':unittest.main(verbosity=2)
