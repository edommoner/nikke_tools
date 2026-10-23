"""Native query order, zero arithmetic, live ignored counts and shared HP admission."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_full_burst_query_cases import fixtures
from portable_full_burst_query_contracts import verify
from world_full_burst_query_native import observe,plain
from portable_specs import LIMITS as L
class FullBurstQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.native=[observe(c) for c in cls.cases]
    def test_literal_order_hp_quantity_and_zero_overflow_contracts(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('Static factory')):self.assertEqual(fixtures(),self.cases)
        for c,(n,t) in zip(self.cases,self.native):verify(c,n,t)
        self.assertEqual(len(self.cases),19)
    def test_observer_preserves_complete_battle_trace_and_rng(self):
        for c,(n,t) in zip(self.cases,self.native):
            b=copy.deepcopy(n);b.pop('full_burst_query');old=sys.getprofile();self.assertEqual((b,t),plain(c));self.assertIs(sys.getprofile(),old)
    def test_query_observation_does_not_add_semantic_calls(self):
        c=next(c for c in self.cases if c['contract']['kind']=='ignored-live-1024')
        def measure(fn):
            counts=[0]*4;get=BuffManager.get_buffs;ref=BuffManager.ref_count;hp=BuffManager.effective_max_hp;sample=random.sample
            def counted_get(self,caster,target,t,exclude_names=frozenset()):counts[0]+=1;return get(self,caster,target,t,exclude_names)
            def counted_ref(self,caster,ref):counts[1]+=1;return ref_orig(self,caster,ref)
            ref_orig=ref
            def counted_hp(self,name,**kw):counts[2]+=1;return hp(self,name,**kw)
            def counted_sample(*a,**kw):counts[3]+=1;return sample(*a,**kw)
            with patch.object(BuffManager,'get_buffs',counted_get),patch.object(BuffManager,'ref_count',counted_ref),patch.object(BuffManager,'effective_max_hp',counted_hp),patch.object(random,'sample',counted_sample):fn(c);state=random.getstate()
            return counts,state
        self.assertEqual(measure(observe),measure(plain))
    def test_order_maximum_latch_and_live_count_faults_rejected(self):
        for c,(n,t) in zip(self.cases,self.native):
            b=copy.deepcopy(n);b['full_burst_query'][0]['percent']+=1
            with self.assertRaises(AssertionError):verify(c,b,t)
            if len(n['full_burst_query'])>1:
                b=copy.deepcopy(n);b['full_burst_query'].reverse()
                with self.assertRaises(AssertionError):verify(c,b,t)
    def test_static_hp_tags_share_wire_with_pending2_and_keep_legacy_gap(self):
        s=importlib.util.spec_from_file_location('query_wire_test',ROOT/'research/verify-world-full-burst-query-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,_=m.prepare();self.assertEqual(len(rows),19)
        for n,w,(c,meta,bindings) in rows:
            row=next(i for i,e in enumerate(c['effects']) if e.get('name')=='landing');self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+row*8+6],2)
            at=L['MODE_BASE']+row*L['MODE_WORDS'];self.assertEqual(w[at+17],0x46424c31)
            if c['contract']['mode']:self.assertEqual(w[at+20:at+22],[0x48504231,1 if c['contract']['mode']=='max_hp_additive' else 2])
        from portable_skill_hp_basis_cases import fixtures as old
        for c in old():
            if c['contract'].get('reference_model_gap'):
                with self.assertRaisesRegex(ValueError,'reference_model_gap'):m.suite.compile_case(c)
    def test_readiness_indexes_scoped_evidence_without_global_promotion(self):
        from portable_readiness_semantics import reference_readiness
        issue=dict(phase='effect',category='fields',kind='damage',stat='sequential_damage:6',target='enemies_random',fields=['land_in_full_burst'])
        r=reference_readiness(issue);self.assertEqual(r['followup_metal_validation']['ordered_query_events'],41);self.assertEqual(r['followup_metal_validation']['inputs'],291)
        for key in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertFalse(r[key])
        self.assertNotIn('live_reentrant_landing_queue_and_capacity_contracts',r['required_extensions'])
    def test_diagnostic_decoder_accepts_saved_word_array_and_rejects_truncation(self):
        import array
        s=importlib.util.spec_from_file_location('query_diag_type_test',ROOT/'research/verify-world-full-burst-query-diagnostic-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        b=array.array('I',[0])*786432;h=L['NATIVE_DIAG_BASE'];b[h]=0x46425131;b[h+8]=12;b[h+9]=128
        self.assertEqual(m.decoded(b,None),[]);self.assertEqual(m.decoded(tuple(b),None),[])
        b[h+3]=1
        with self.assertRaises(AssertionError):m.decoded(b,None)
    def test_exact_source_proof_rejects_query_order_and_zero_calculation_regressions(self):
        from portable_full_burst_landing_source_contract import project_sources
        project_sources(ROOT)
        for name,old,new in [('gpu/program_phases.slang','initializeNativeQueryDiagnostic(s)','initializeWrongDiagnostic(s)'),('gpu/hp_attack_runtime.slang','if(parentRow<s.count)','if(false)'),('gpu/dispatch_phases.slang','queryOnlyFullBurstLanding','sampleFullBurstLanding'),('gpu/damage_runtime.slang','readFullBurstLandingReference(s,basisRow,when)','fullBurstLandingCount(s,basisRow)'),('gpu/skill_hp_basis_runtime.slang','deferredInvalid && d.damagePending!=2','false')]:
            s=(ROOT/name).read_text();self.assertIn(old,s)
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:s.replace(old,new)})
if __name__=='__main__':unittest.main()
