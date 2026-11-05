"""Storage bytecode/readback validation must complete before any CUDA load."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sp=importlib.util.spec_from_file_location('storage_boundaries',ROOT/'scripts/verify-healing-storage.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);v=m.v;g=m.g
class HealingStorageBoundaries(unittest.TestCase):
    def setUp(self):
        b=v.body(1);b['enemy']['patterns']=[]
        with v.s.v.context('storage-boundary',{v.N[0]:[v.B('reserve','heal_overcharge_store',5)]}):self.compiled=v.s.v.v.a.evaluate({**b,'_compile_detail':True})
    def test_storage_is_distinct_from_HP_shield_decoy_stats(self):
        q=self.compiled['program']['effects'][0];self.assertEqual((q[1],q[2],q[6],q[207]),(0,74,5,0))
    def test_instant_storage_form_still_rejects(self):
        with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(v.E('wrong type','instant','heal_overcharge_store',5),v.N[0])])
    def test_zero_negative_and_stacked_capacities_have_real_storage_opcode(self):
        for value in (-10,0,5):
            p=g.compile_effects(self.compiled['program']['chars'],[(v.B('reserve','heal_overcharge_store',value,max_stack=5,event='every:0.1s'),v.N[0])]);self.assertTrue(all(q[1]==0 and q[2]==74 and q[6]==value and q[9]==5 for q in p['effects']))
    def test_CPU_storage_extension_rebinds_the_actual_runner(self):
        from calculator import timeline
        from runner import sim
        self.assertIs(sim.simulate,timeline.simulate);self.assertTrue(getattr(v.BuffManager,'_nikke_healing_storage',False))
if __name__=='__main__':unittest.main()
