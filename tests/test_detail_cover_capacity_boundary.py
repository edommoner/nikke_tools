"""Reject malformed max-HP reference flags before loading CUDA."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('capacity_bounds',ROOT/'scripts/verify-cover-capacity.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);g=v.g
class CoverCapacityBoundaries(unittest.TestCase):
    def setUp(self):
        b=v.v.body(1);b['enemy']['patterns']=[]
        with v.v.s.v.context('capacity-boundary',{v.N[0]:[v.B('cover max','cover_hp_pct',20,scaling='max_hp')]}):self.compiled=v.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    def reject(self,p):
        with patch.object(g,'module_image',side_effect=AssertionError('CUDA must not be reached')):
            with self.assertRaisesRegex(ValueError,'maximum-HP value reference'):g.run(object(),[p],[[0,2,101,0,0,0,0,0]],[self.compiled['enemy']],[self.compiled['base_stats']])
    def test_capacity_marker_is_distinct_from_stack_scaling(self):
        q=self.compiled['program']['effects'][0];self.assertEqual((q[1],q[2],q[10],q[50],q[258]),(0,70,-1,1,0))
    def test_preexisting_caster_maximum_healing_stays_supported(self):
        for stat,kind in [('heal_hp_pct',6),('cover_heal_pct',7),('shield_heal_pct',27)]:
            p=g.compile_effects(self.compiled['program']['chars'],[(v.E('heal','instant',stat,10,scaling='max_hp'),v.N[0])]);self.assertEqual((p['effects'][0][1],p['effects'][0][50]),(kind,1))
    def test_other_stats_do_not_silently_gain_maximum_HP_scaling(self):
        for e in [v.B('bad','atk_pct',10,scaling='max_hp'),v.E('bad','instant','cover_revive',10,scaling='max_hp')]:
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
    def test_malformed_reference_flags_are_rejected(self):
        for flag in (-1,.5,2):
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][50]=flag;self.reject(p)
    def test_wrong_carrier_type_stat_and_value_mode_are_rejected(self):
        for column,value in ((1,4),(2,0),(10,-3),(258,1)):
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][column]=value;self.reject(p)
    def test_stacks_and_bullet_lifetimes_keep_the_reference(self):
        p=g.compile_effects(self.compiled['program']['chars'],[(v.B('stacked','cover_hp_pct',10,scaling='max_hp',max_stack=3,duration_bullets=2,event='every:0.1s'),v.N[0])]);self.assertTrue(all(q[50]==1 and q[10]==-1 for q in p['effects']))
if __name__=='__main__':unittest.main()
