"""Validate decoy-heal bytecode and readback addresses before CUDA."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('decoy_bounds',ROOT/'scripts/verify-decoy-healing.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);g=v.g
class DecoyHealingBoundaries(unittest.TestCase):
    def setUp(self):
        b=v.v.body(1);b['enemy']['patterns']=[]
        with v.v.s.v.context('decoy-boundary',{v.N[0]:[v.E('repair','instant','decoy_heal_pct',1,scaling='max_hp')]}):self.compiled=v.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    def reject(self,p,pattern,script=None):
        with patch.object(g,'module_image',side_effect=AssertionError('CUDA must not be reached')):
            with self.assertRaisesRegex(ValueError,pattern):g.run(object(),[p],script or [[0,2,101,0,0,0,0,0]],[self.compiled['enemy']],[self.compiled['base_stats']])
    def test_decoy_heal_has_its_own_kind_and_caster_reference(self):
        q=self.compiled['program']['effects'][0];self.assertEqual((q[1],q[50],q[258]),(31,1,1))
    def test_enemy_healing_and_buff_form_do_not_silently_compile(self):
        for e in [v.E('bad','instant','decoy_heal_pct',1,'target'),v.B('bad','decoy_heal_pct',1)]:
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
    def test_wrong_kind_metadata_and_target_are_rejected(self):
        for column,value in [(258,0),(4,4)]:
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][column]=value
            if column==258:p['effects'][0][50]=0
            self.reject(p,'decoy healing instruction')
    def test_unknown_maximum_reference_flags_are_rejected(self):
        for flag in (-1,.5,2):
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][50]=flag;self.reject(p,'maximum-HP value reference')
    def test_decoy_queries_reject_fractional_and_out_of_bounds_keys(self):
        for key in (-2,.5,g.NE):self.reject(self.compiled['program'],'decoy state query',[[0,2,121,0,key,0,0,0]])
    def test_frame_witness_requires_boolean(self):
        for flag in (None,1,'yes'):
            c=copy.deepcopy(self.compiled);c['body']['_debug_decoy_frames']=flag
            with patch.object(g,'run',side_effect=AssertionError('CUDA must not be reached')),self.assertRaisesRegex(ValueError,'decoy frame witness'):g.evaluate_full(object(),c)
    def test_zero_negative_and_periodic_base_values_are_valid(self):
        for value in (-1,0,1):
            p=g.compile_effects(self.compiled['program']['chars'],[(v.E('repair','instant','decoy_heal_pct',value,tick_interval=.2,duration=1),v.N[0])]);self.assertTrue(all(q[1]==31 and q[6]==value for q in p['effects']))
if __name__=='__main__':unittest.main()
