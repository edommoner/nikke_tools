"""Native phase/count/ordering contracts before common GPU admission."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,portable_backend,detail_gpu
from calculator.buff_manager import BuffManager
from calculator import timeline
from portable_full_burst_landing_cases import fixtures
from portable_full_burst_landing_contracts import verify,verify_trace
from world_full_burst_landing_native import observe,plain
from portable_full_burst_landing_roster_cases import fixtures as real
from portable_full_burst_landing_roster_contracts import verify as verify_real
from world_full_burst_landing_roster_native import observe as observe_real
class FullBurstLandingReferenceTests(unittest.TestCase):
    def test_literal_contracts_before_packing_or_gpu(self):
        def no(*a,**kw):raise AssertionError('Packing/GPU forbidden')
        with patch.object(timeline,'simulate',no):cases=fixtures()+real()
        self.assertEqual(len(cases),15);before=copy.deepcopy(cases)
        with patch.object(portable_runtime,'compile_program',no),patch.object(detail_gpu,'compile_effects',no),patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no):
            for c in cases:
                if 'body' in c:verify_real(c,observe_real(c)[0])
                else:n,t=observe(c);verify(c,n);verify_trace(c,t)
        self.assertEqual(before,cases)
    def test_observer_keeps_battle_trace_rng_and_query_calls(self):
        for c in fixtures()+real():
            def bare_real(case):
                s=importlib.util.spec_from_file_location('landing_equivalence_real',ROOT/'research/verify-world-projectile-rosters.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);n,shots=m.native_reference(case['body']);return dict(battle=n,projectile_shots=shots),[]
            def measured(fn):
                original=sys.getprofile()
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'ref_count',autospec=True,side_effect=BuffManager.ref_count) as ref,patch.object(BuffManager,'_by_name',autospec=True,side_effect=BuffManager._by_name) as named,patch.object(BuffManager,'notify',autospec=True,side_effect=BuffManager.notify) as notify,patch.object(random,'sample',side_effect=random.sample) as sample:
                    answer=fn(c);counts=[m.call_count for m in (get,ref,named,notify,sample)];state=random.getstate()
                self.assertIs(sys.getprofile(),original);return answer,counts,state
            (n,t),counts,state=measured(observe_real if 'body' in c else observe);n.pop('full_burst_landing');(p,trace),old,prior=measured(bare_real if 'body' in c else plain)
            with self.subTest(case=c['name']):self.assertEqual((n,t,counts,state),(p,trace,old,prior))
    def test_faults_in_latch_scope_time_reads_and_full_burst_rejected(self):
        c=next(c for c in fixtures() if c['contract']['reference']);n,t=observe(c)
        for fault in ('latched','excluded','time','full','reads','notifications','owner'):
            b=copy.deepcopy(n);o=b['full_burst_landing'];r=o['calls'][1]
            if fault=='latched':r['latched']=2
            elif fault=='excluded':r['excluded']=[]
            elif fault=='time':r['time']=o['calls'][0]['time']
            elif fault=='full':r['full']=False
            elif fault=='reads':o['count_reads'].pop()
            elif fault=='owner':r['owner']=4
            else:o['hits']=[]
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,b)
        b=copy.deepcopy(t);b[0]['amount']+=1
        with self.assertRaises(AssertionError):verify_trace(c,b)
    def test_gpu_admission_remains_closed(self):
        for c in fixtures():
            e=next(e for e in c['effects'] if e.get('name')=='landing')
            with self.assertRaises(ValueError):portable_runtime.validate_effect(e,combat=c['combat'],world_frame=True)
    def test_native_source_routing_preserves_unproven_fields(self):
        from portable_readiness_semantics import reference_readiness
        for stat in ('sequential_damage:6','sequential_damage:13'):
            issue=dict(phase='effect',category='fields',kind='damage',stat=stat,target='enemies_random',fields=['land_in_full_burst'])
            r=reference_readiness(issue);self.assertEqual(r['lane'],'native_contract_extension');self.assertEqual(r['recorded_cases'],15);self.assertFalse(r['gpu_supported']);self.assertFalse(r['runtime_validation_performed'])
            self.assertEqual(reference_readiness(dict(issue,fields=['land_in_full_burst','unknown']))['lane'],'reference_review')
if __name__=='__main__':unittest.main()
