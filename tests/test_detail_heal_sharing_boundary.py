"""Staged bytecode validation, before loading any CUDA module."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('sharing_definitions',ROOT/'scripts/heal-sharing-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);g=d.g;v=d.v
class Boundaries(unittest.TestCase):
    def setUp(self):
        b=v.body(1);b['enemy']['patterns']=[]
        with v.s.v.context('sharing-boundary',{v.N[0]:[v.B('link','heal_split',1,'all_allies')]}):self.compiled=v.s.v.v.a.evaluate({**b,'_compile_detail':True})
    def test_real_marker_opcode(self):
        q=self.compiled['program']['effects'][0];self.assertEqual((q[1],q[2]),(0,75))
    def test_wrong_healing_effect_types_rejected(self):
        for e in [v.E('wrong type','instant','heal_split',1),v.E('wrong type','instant','heal_overcharge_store_atk_pct',1),v.B('wrong type','heal_overcharge_discharge',1,target_effect='pool')]:
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
    def test_CPU_extension_idempotence_and_runner_binding(self):
        from calculator import timeline
        from runner import sim
        import heal_sharing_compat
        current=timeline.simulate;heal_sharing_compat.install();self.assertIs(current,timeline.simulate);self.assertIs(sim.simulate,current)
if __name__=='__main__':unittest.main()
