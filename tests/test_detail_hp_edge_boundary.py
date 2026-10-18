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
            self.compiled=v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    def run_bad(self,program,script,match):
        with patch.object(g,'module_image',side_effect=AssertionError('CUDA must not be reached')):
            with self.assertRaisesRegex(ValueError,match):g.run(object(),[program],script,[self.compiled['enemy']],[self.compiled['base_stats']])
    def test_fractional_threshold_keeps_distinct_HP_event_code(self):
        d=self.compiled['program']['effects'][0][g.TD:g.TD+g.TS]
        self.assertEqual((d[0],d[4],d[6]),(48,60.125,-11))
    def test_nonfinite_and_invalid_counted_timings_fail_compilation(self):
        chars=self.compiled['program']['chars']
        for timing in ('hp_below:nan','hp_below:inf','event:ally_hp_below:-inf','hp_below_count:60:0','hp_below_count:60:-1','hp_below_count:60:1:2','event:adjacent_hp_below:60:oops'):
            with self.subTest(timing=timing),self.assertRaises(g.UnsupportedDetail):g.compile_effects(chars,[(v.B('invalid','atk_pct',1,event=timing),v.N[0])])
    def test_private_continuation_events_are_never_authored_inputs(self):
        for event in (52,53):
            self.run_bad(self.compiled['program'],[[0,0,event,0,0,-1,0,0],[0,2,101,0,0,0,0,0]],'private HP')
    def test_HP_descriptor_markers_tags_and_event_codes_are_checked(self):
        for index,value in ((0,31),(3,-1),(6,-15)):
            program=copy.deepcopy(self.compiled['program']);program['effects'][0][g.TD+index]=value
            self.run_bad(program,[[0,2,101,0,0,0,0,0]],'HP transition descriptor')
    def test_HP_log_query_rejects_invalid_addresses_before_CUDA(self):
        for index in (-1,1024,.5):self.run_bad(self.compiled['program'],[[0,2,120,0,index,0,0,0]],'HP event log query')
if __name__=='__main__':unittest.main(verbosity=2)
