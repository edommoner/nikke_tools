"""Reject unknown/fractional healing opcodes before loading any CUDA module."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('outgoing_bounds',ROOT/'scripts/verify-outgoing-healing.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);g=v.g
class OutgoingHealingBoundaries(unittest.TestCase):
    def setUp(self):
        b=v.v.body(1);b['enemy']['patterns']=[]
        with v.v.s.v.context('outgoing-boundary',{v.N[0]:[v.B('outgoing','outgoing_heal_pct',50)]}):self.compiled=v.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    def test_outgoing_is_a_distinct_direct_read_buff(self):
        q=self.compiled['program']['effects'][0];self.assertEqual((q[1],q[2],q[6],q[207]),(0,73,50,0))
    def test_unknown_and_fractional_stat_codes_rejected_before_cuda(self):
        for key in (-1,73.5,10000):
            with self.subTest(key=key):
                p=copy.deepcopy(self.compiled['program']);p['effects'][0][2]=key
                with patch.object(g,'module_image',side_effect=AssertionError('CUDA must not be reached')),self.assertRaisesRegex(ValueError,'Invalid compiled detailed effect'):
                    g.run(object(),[p],[[0,2,101,0,0,0,0,0]],[self.compiled['enemy']],[self.compiled['base_stats']])
    def test_instant_form_does_not_silently_compile(self):
        with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(v.E('bad','instant','outgoing_heal_pct',50),v.N[0])])
    def test_zero_negative_and_stacked_bonuses_are_representable(self):
        for value in (-150,0,50):
            p=g.compile_effects(self.compiled['program']['chars'],[(v.B('bonus','outgoing_heal_pct',value,event='every:0.1s',max_stack=3),v.N[0])])
            self.assertTrue(all(q[1]==0 and q[2]==73 and q[6]==value and q[9]==3 for q in p['effects']))
    def test_cpu_extension_is_installed_at_both_simulation_entry_points(self):
        from runner import sim
        from calculator import timeline
        self.assertIs(sim.simulate,timeline.simulate)
        self.assertTrue(getattr(v.BuffManager.heal_received_mult,'_nikke_outgoing_healing',False))
if __name__=='__main__':unittest.main()
