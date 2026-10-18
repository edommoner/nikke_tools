"""Storage bytecode/readback validation must complete before any CUDA load."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sp=importlib.util.spec_from_file_location('storage_boundaries',ROOT/'scripts/verify-staged-healing-storage.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);v=m.v;g=m.g
class HealingStorageBoundaries(unittest.TestCase):
    def setUp(self):
        b=v.body(1);b['enemy']['patterns']=[]
        with v.s.v.context('storage-boundary',{v.N[0]:[v.B('reserve','heal_overcharge_store',5)]}):self.compiled=v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    def reject(self,p,pattern,script=None):
        with patch.object(g,'module_image',side_effect=AssertionError('CUDA must not be reached')),self.assertRaisesRegex(ValueError,pattern):g.run(object(),[p],script or [[0,2,101,0,0,0,0,0]],[self.compiled['enemy']],[self.compiled['base_stats']])
    def test_storage_is_distinct_from_HP_shield_decoy_stats(self):
        q=self.compiled['program']['effects'][0];self.assertEqual((q[1],q[2],q[6],q[207]),(0,74,5,0))
    def test_unknown_or_fractional_stat_codes_rejected(self):
        for key in (-1,74.5,75):
            p=copy.deepcopy(self.compiled['program']);p['effects'][0][2]=key;self.reject(p,'Invalid compiled detailed effect')
    def test_storage_query_key_range_rejected_before_cuda(self):
        for key in (-2,.5,g.NE):self.reject(self.compiled['program'],'healing-storage query',[[0,2,122,0,key,0,0,0]])
    def test_storage_debug_flag_requires_bool(self):
        for flag in (None,1,'yes'):
            c=copy.deepcopy(self.compiled);c['body']['_debug_storage_frames']=flag
            with patch.object(g,'run',side_effect=AssertionError('CUDA must not be reached')),self.assertRaisesRegex(ValueError,'storage frame witness'):g.evaluate_full(object(),c)
    def test_other_healing_families_still_reject(self):
        for e in (v.B('separate','heal_overcharge_store_atk_pct',5),v.B('separate','heal_split',1),v.E('separate','instant','heal_overcharge_discharge',0,target_effect='reserve'),v.E('wrong type','instant','heal_overcharge_store',5)):
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
    def test_zero_negative_and_stacked_capacities_have_real_storage_opcode(self):
        for value in (-10,0,5):
            p=g.compile_effects(self.compiled['program']['chars'],[(v.B('reserve','heal_overcharge_store',value,max_stack=5,event='every:0.1s'),v.N[0])]);self.assertTrue(all(q[1]==0 and q[2]==74 and q[6]==value and q[9]==5 for q in p['effects']))
    def test_CPU_storage_extension_rebinds_the_actual_runner(self):
        from calculator import timeline
        from runner import sim
        self.assertIs(sim.simulate,timeline.simulate);self.assertTrue(getattr(v.BuffManager,'_nikke_healing_storage',False))
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HealingStorageBoundaries))
    files=['research/test_staged_healing_storage_boundaries.py','scripts/verify-staged-healing-storage.py','research/probe-healing-storage-squads.py','scripts/staged-healing-storage-runtime.py','research/staging/v40/app/detail_gpu.py','research/staging/v40/app/healing_storage_compat.py','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py']
    r=dict(passed=result.wasSuccessful() and not result.skipped,tests_run=result.testsRun,skipped=len(result.skipped),gpu_run=False,stage_only=True,objective_complete=False,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files});(ROOT/'research/detail-healing-storage-boundary-verification.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
