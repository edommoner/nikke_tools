"""Staged bytecode validation, before loading any CUDA module."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('sharing_definitions',ROOT/'research/heal-sharing-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);g=d.g;v=d.v
class Boundaries(unittest.TestCase):
    def setUp(self):
        b=v.body(1);b['enemy']['patterns']=[]
        with v.s.v.context('sharing-boundary',{v.N[0]:[v.B('link','heal_split',1,'all_allies')]}):self.compiled=v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    def reject(self,p,pattern,script=None):
        with patch.object(g,'module_image',side_effect=AssertionError('CUDA must not be reached')),self.assertRaisesRegex(ValueError,pattern):g.run(object(),[p],script or [[0,2,101,0,0,0,0,0]],[self.compiled['enemy']],[self.compiled['base_stats']])
    def test_real_marker_opcode(self):
        q=self.compiled['program']['effects'][0];self.assertEqual((q[1],q[2]),(0,75))
    def test_unknown_fractional_and_nonfinite_stat_rejected(self):
        for key in (-1,75.5,10000,float('nan'),float('inf')):
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][2]=key;self.reject(p,'Invalid compiled detailed effect')
    def test_private_continuations_cannot_be_authored(self):
        for event in (52,53,54):self.reject(self.compiled['program'],'private HP continuation',[[0,0,event,0,0,0,0,0],[0,2,101,0,0,0,0,0]])
    def test_wrong_type_and_separate_storage_families_rejected(self):
        for e in [v.E('wrong type','instant','heal_split',1),v.B('ATK storage','heal_overcharge_store_atk_pct',1),v.E('discharge','instant','heal_overcharge_discharge',0)]:
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
    def test_CPU_extension_idempotence_and_runner_binding(self):
        from calculator import timeline
        from runner import sim
        import heal_sharing_compat
        current=timeline.simulate;heal_sharing_compat.install();self.assertIs(current,timeline.simulate);self.assertIs(sim.simulate,current)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Boundaries))
    files=['research/probe-heal-sharing-boundaries.py','research/staging/v41/app/detail_gpu.py','research/staging/v41/app/heal_sharing_compat.py','scripts/staged-heal-sharing-runtime.py','app/healing_storage_compat.py','app/engine_compat.py']
    report=dict(passed=result.wasSuccessful(),tests_run=result.testsRun,gpu_loaded=False,stage_only=True,objective_complete=False,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
    (ROOT/'research/detail-heal-sharing-boundaries.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if result.wasSuccessful() else 1)
