"""Reject malformed charge/discharge bytecode before loading a CUDA module."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('charge_definitions',ROOT/'research/heal-charge-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);g=d.g;v=d.v
class Boundaries(unittest.TestCase):
    def setUp(self):
        name,b,x=next(d.fixtures());b['enemy']['patterns']=[]
        with v.s.v.context(name,x):self.compiled=v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    def reject(self,program,pattern,script=None):
        with patch.object(g,'module_image',side_effect=AssertionError('CUDA must not be reached')),self.assertRaisesRegex(ValueError,pattern):g.run(object(),[program],script or [[0,2,101,0,0,0,0,0]],[self.compiled['enemy']],[self.compiled['base_stats']])
    def test_distinct_opcodes_and_named_reference(self):
        rows=self.compiled['program']['effects'];self.assertTrue(any(r[1]==0 and r[2]==76 for r in rows));self.assertTrue(any(r[1]==32 and r[258]==1 for r in rows))
        p=g.compile_effects(self.compiled['program']['chars'],[(v.B('limit','accumulate_max_scale_pct',20,target_effect='IFAK fixture'),v.N[0])]);self.assertTrue(any(r[1]==0 and r[2]==77 and r[212]==1 for r in p['effects']))
    def test_required_discharge_reference(self):
        for ref in (None,'',[],3):
            with self.assertRaisesRegex(g.UnsupportedDetail,'named target_effect'):g.compile_effects(self.compiled['program']['chars'],[(v.E('release','instant','heal_overcharge_discharge',0,target_effect=ref),v.N[0])])
    def test_unknown_or_fractional_instruction_kinds(self):
        for key in (-2,32.5,10000):
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][1]=key;self.reject(p,'instruction kind')
    def test_unknown_or_fractional_stat_codes(self):
        for key in (-1,77.5,10000):
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][2]=key;self.reject(p,'compiled detailed effect')
    def test_discharge_reference_and_type_validation(self):
        index=next(i for i,r in enumerate(self.compiled['program']['effects']) if r[1]==32)
        for field,value in [(36,-1),(36,g.NE),(36,.5),(258,0)]:
            p=copy.deepcopy(self.compiled['program']);p['effects'][index][field]=value;self.reject(p,'healing discharge instruction')
    def test_query_bounds(self):
        for key in (-2,.5,g.NE):self.reject(self.compiled['program'],'healing-charge query',[[0,2,123,0,key,0,0,0]])
    def test_debug_flag_requires_boolean(self):
        for flag in (None,1,'yes'):
            c=copy.deepcopy(self.compiled);c['body']['_debug_charge_frames']=flag
            with patch.object(g,'run',side_effect=AssertionError('CUDA must not be reached')),self.assertRaisesRegex(ValueError,'charge frame witness'):g.evaluate_full(object(),c)
    def test_wrong_effect_types_still_reject(self):
        for e in [v.E('bad','instant','heal_overcharge_store_atk_pct',20),v.E('bad','instant','accumulate_max_scale_pct',20),v.B('bad','heal_overcharge_discharge',1,target_effect='pool')]:
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
    def test_capacity_reference_flags(self):
        with v.s.v.context('charge-boundary',{v.N[0]:[v.B('bonus','accumulate_max_scale_pct',20,target_effect='pool')]}):compiled=v.s.v.v.a.evaluate({**self.compiled['body'],'_compile_gpu_detail':True})
        index=next(i for i,r in enumerate(compiled['program']['effects']) if r[1]==0 and r[2]==77)
        for field,value in [(212,.5),(36,-1),(36,g.NE)]:
            p=copy.deepcopy(compiled['program']);p['effects'][index][field]=value;self.reject(p,'healing capacity reference')
    def test_CPU_extension_idempotence_and_binding(self):
        from calculator import timeline
        from runner import sim
        import heal_charge_compat
        before=timeline._register_instant_handlers;heal_charge_compat.install();self.assertIs(before,timeline._register_instant_handlers);self.assertIs(timeline.simulate,sim.simulate)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Boundaries))
    files=['research/probe-heal-charge-boundaries.py','research/heal-charge-fixtures.py','research/staging/v42/app/detail_gpu.py','research/staging/v42/app/heal_charge_compat.py','scripts/staged-heal-charge-runtime.py','app/engine_compat.py']
    r=dict(passed=result.wasSuccessful(),tests_run=result.testsRun,gpu_loaded=False,stage_only=True,objective_complete=False,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
    (ROOT/'research/detail-heal-charge-boundaries.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if result.wasSuccessful() else 1)
