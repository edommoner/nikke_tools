"""Reject malformed charge/discharge bytecode before loading a CUDA module."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('charge_definitions',ROOT/'scripts/heal-charge-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);g=d.g;v=d.v
class Boundaries(unittest.TestCase):
    def setUp(self):
        name,b,x=next(d.fixtures());b['enemy']['patterns']=[]
        with v.s.v.context(name,x):self.compiled=v.s.v.v.a.evaluate({**b,'_compile_detail':True})
    def test_distinct_opcodes_and_named_reference(self):
        rows=self.compiled['program']['effects'];self.assertTrue(any(r[1]==0 and r[2]==76 for r in rows));self.assertTrue(any(r[1]==32 and r[258]==1 for r in rows))
        p=g.compile_effects(self.compiled['program']['chars'],[(v.B('limit','accumulate_max_scale_pct',20,target_effect='IFAK fixture'),v.N[0])]);self.assertTrue(any(r[1]==0 and r[2]==77 and r[212]==1 for r in p['effects']))
    def test_required_discharge_reference(self):
        for ref in (None,'',[],3):
            with self.assertRaisesRegex(g.UnsupportedDetail,'named target_effect'):g.compile_effects(self.compiled['program']['chars'],[(v.E('release','instant','heal_overcharge_discharge',0,target_effect=ref),v.N[0])])
    def test_wrong_effect_types_still_reject(self):
        for e in [v.E('bad','instant','heal_overcharge_store_atk_pct',20),v.E('bad','instant','accumulate_max_scale_pct',20),v.B('bad','heal_overcharge_discharge',1,target_effect='pool')]:
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
    def test_CPU_extension_idempotence_and_binding(self):
        from calculator import timeline
        from runner import sim
        import heal_charge_compat
        before=timeline._register_instant_handlers;heal_charge_compat.install();self.assertIs(before,timeline._register_instant_handlers);self.assertIs(timeline.simulate,sim.simulate)
if __name__=='__main__':unittest.main()
