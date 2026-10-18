"""Pre-CUDA grammar checks and the independently observed CPU None contract."""
import copy,importlib.util,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import engine_compat as loader
import detail_gpu as g
sp=importlib.util.spec_from_file_location('scaling_bound_oracle',ROOT/'scripts/verify-survival-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
from calculator.buff_manager import BuffManager

class ScalingAndCoverBoundaries(unittest.TestCase):
    def setUp(self):
        b=v.v.body(1);b['enemy']['patterns']=[]
        with v.v.context('controlled',{v.N[0]:[v.B('scaled','atk_pct',1.5,scaling='lost_hp_pct')]}):self.compiled=v.v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    def reject(self,program,pattern):
        with patch.object(g,'module_image',side_effect=AssertionError('CUDA must not be reached')):
            with self.assertRaisesRegex(ValueError,pattern):g.run(object(),[program],[[0,2,101,0,0,0,0,0]],[self.compiled['enemy']],[self.compiled['base_stats']])
    def test_lost_HP_mode_is_explicit_and_not_stack_capture(self):
        self.assertEqual(self.compiled['program']['effects'][0][10],-3)
    def test_invalid_scaling_modes_are_rejected_before_CUDA(self):
        for value in (-4,.5,g.NE):
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][10]=value;self.reject(p,'value scaling mode')
        p=copy.deepcopy(self.compiled['program']);p['effects'][0][258]=1;self.reject(p,'value scaling mode')
    def test_cover_revive_zero_and_wrong_scaling_do_not_silently_compile(self):
        chars=self.compiled['program']['chars']
        for value,kw in [(0,{}),(10,{'scaling':'lost_hp_pct'}),(10,{'scaling':'max_hp'})]:
            with self.subTest(value=value,kw=kw),self.assertRaises(g.UnsupportedDetail):g.compile_effects(chars,[(v.E('bad','instant','cover_revive',value,**kw),v.N[0])])
    def test_broken_cover_random_count_clamps_to_roster_and_preserves_zero(self):
        for count,expected in ((0,0),(2,2),(99,5)):
            p=g.compile_effects(self.compiled['program']['chars'],[(v.E('revive','instant','cover_revive',50,'allies_broken_cover_random:'+str(count)),v.N[0])]);q=p['effects'][0];self.assertEqual((q[1],q[4],q[5]),(30,25,expected))
    def test_bad_cover_counts_and_wrong_instant_kind_are_rejected_before_CUDA(self):
        p=g.compile_effects(self.compiled['program']['chars'],[(v.E('revive','instant','cover_revive',50,'allies_broken_cover_random:2'),v.N[0])])
        for count in (-1,.5,6):
            c=copy.deepcopy(p);c['effects'][0][5]=count;self.reject(c,'broken-cover target count')
        p['effects'][0][258]=0;self.reject(p,'cover revival instruction')
    def test_scalar_witness_addresses_are_validated_before_launch(self):
        for scalar in ({'who':5,'key':0},{'who':0,'key':32},{'who':0.5,'key':0},{'who':0}):
            c=copy.deepcopy(self.compiled);c['body']['_debug_scalar_query']=scalar
            with patch.object(g,'run',side_effect=AssertionError('CUDA must not be reached')),self.assertRaisesRegex(ValueError,'scalar frame witness'):g.evaluate_full(object(),c)

class CPURevivalScalingContext(unittest.TestCase):
    def value(self,pct,context=None,base=1.5):
        bm=object.__new__(BuffManager);bm.state={'hp_pct':{'source':pct}}
        if context is not None:bm._nikke_revive_percentages={'source':context}
        ab=SimpleNamespace(caster='source',stack=3)
        eff={'fixed_value':base,'scaling':'lost_hp_pct','max_stack':3}
        return bm,ab,eff
    def test_ordinary_query_uses_live_percentage_and_ignores_stacks(self):
        bm,ab,e=self.value(50);self.assertEqual(bm._get_value(e,ab),75);self.assertEqual(bm.state['hp_pct']['source'],50)
    def test_revival_query_restores_None_without_synchronizing_HP(self):
        bm,ab,e=self.value(None,50)
        with patch.object(BuffManager,'sync_hp',side_effect=AssertionError('No transition permitted')):self.assertEqual(bm._get_value(e,ab),75)
        self.assertIsNone(bm.state['hp_pct']['source'])
    def test_None_outside_revival_keeps_original_exception(self):
        bm,ab,e=self.value(None)
        with self.assertRaises(TypeError):bm._get_value(e,ab)
    def test_query_exception_restores_transition_sentinel(self):
        bm,ab,e=self.value(None,50,'invalid')
        with self.assertRaises(ValueError):bm._get_value(e,ab)
        self.assertIsNone(bm.state['hp_pct']['source'])
    def test_context_install_is_idempotent(self):
        current=BuffManager._get_value;loader.install();self.assertIs(BuffManager._get_value,current)
if __name__=='__main__':unittest.main(verbosity=2)
