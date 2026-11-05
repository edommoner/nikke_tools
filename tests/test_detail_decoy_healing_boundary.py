"""Validate decoy-heal bytecode and readback addresses before CUDA."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('decoy_bounds',ROOT/'scripts/verify-decoy-healing.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);g=v.g
class DecoyHealingBoundaries(unittest.TestCase):
    def setUp(self):
        b=v.v.body(1);b['enemy']['patterns']=[]
        with v.v.s.v.context('decoy-boundary',{v.N[0]:[v.E('repair','instant','decoy_heal_pct',1,scaling='max_hp')]}):self.compiled=v.v.s.v.v.a.evaluate({**b,'_compile_detail':True})
    def test_decoy_heal_has_its_own_kind_and_caster_reference(self):
        q=self.compiled['program']['effects'][0];self.assertEqual((q[1],q[50],q[258]),(31,1,1))
    def test_enemy_healing_and_buff_form_do_not_silently_compile(self):
        for e in [v.E('bad','instant','decoy_heal_pct',1,'target'),v.B('bad','decoy_heal_pct',1)]:
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
    def test_zero_negative_and_periodic_base_values_are_valid(self):
        for value in (-1,0,1):
            p=g.compile_effects(self.compiled['program']['chars'],[(v.E('repair','instant','decoy_heal_pct',value,tick_interval=.2,duration=1),v.N[0])]);self.assertTrue(all(q[1]==31 and q[6]==value for q in p['effects']))
if __name__=='__main__':unittest.main()
