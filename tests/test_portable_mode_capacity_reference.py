"""Pinned native magazine memo contracts, with no portable admission or GPU."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_mode_capacity_cases import fixtures
from portable_mode_capacity_contracts import verify
import world_mode_capacity_native as observer
from world_projectile_native import observe as plain_observe
import portable_backend,portable_runtime,detail_gpu

class ModeCapacityReferenceTests(unittest.TestCase):
    def test_literal_contracts_without_packing_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases)
        def forbidden(*a,**kw):raise AssertionError('GPU/packing forbidden in native contracts')
        with patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):
                    native,_=observer.observe(case);self.assertTrue(verify(case,native)['verified'])
        self.assertEqual(cases,before)
    def test_observer_preserves_all_existing_battle_fields_and_trace(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                expected,trace=plain_observe(case);actual,observed=observer.observe(case)
                actual.pop('mode_capacity');self.assertEqual(actual,expected);self.assertEqual(observed,trace)
    def test_cache_hit_capacity_ref_query_and_mode_exit_faults_reject(self):
        case=next(c for c in fixtures() if c['name']=='mode-capacity-gauge-three');native,_=observer.observe(case)
        for kind in ('capacity','reference-read','mode-hit','exit'):
            changed=copy.deepcopy(native);obs=changed['mode_capacity']
            if kind=='capacity':next(q for q in obs['queries'] if q['reference_mode'])['value']+=1
            elif kind=='reference-read':obs['references'].pop()
            elif kind=='mode-hit':obs['frames'][0]['hits']+=1
            else:next(f for f in obs['frames'] if f['after']['restored'])['after']['restored']=False
            with self.subTest(kind=kind),self.assertRaises(AssertionError):verify(case,changed)
    def test_zero_is_not_missing_and_infinite_ammo_still_fires_once(self):
        cases={c['name']:c for c in fixtures()}
        missing,_=observer.observe(cases['mode-capacity-missing']);zero,_=observer.observe(cases['mode-capacity-gauge-zero'])
        self.assertEqual([q['value'] for q in missing['mode_capacity']['references']],[None,None])
        self.assertEqual([q['value'] for q in zero['mode_capacity']['references']],[0,0])
        self.assertEqual(cases['mode-capacity-zero-infinite-ammo']['contract']['mode_shots'],1)
        self.assertEqual(cases['mode-capacity-zero-charge']['contract']['mode_shots'],0)
    def test_reload_and_entry_snapshot_policies_are_separate(self):
        cases={c['name']:c for c in fixtures()}
        for label in ('reload-resamples','persistent-zero-reloads'):
            c=cases['mode-capacity-'+label];self.assertNotIn('duration_bullets',c['effects'][-1]);self.assertNotIn('duration',c['effects'][-1])
        no_reload=cases['mode-capacity-bullet-limit-prevents-reload'];self.assertEqual(no_reload['effects'][-1]['duration_bullets'],99);self.assertEqual(no_reload['contract']['capacities'],[2])
        entry=cases['mode-capacity-entry-delay-resamples'];self.assertTrue(entry['effects'][-1]['entry_reload']);self.assertEqual(entry['contract']['capacities'],[2,4])
    def test_profile_composes_and_restores_on_failure(self):
        previous=sys.getprofile();calls=[]
        def prior(frame,event,result):
            if event=='call' and frame.f_code is observer.BuffManager.ref_count.__code__:calls.append(event)
        try:
            sys.setprofile(prior);observer.observe(fixtures()[0]);self.assertEqual(len(calls),2);self.assertIs(sys.getprofile(),prior)
            with patch.object(observer,'projectile_native',side_effect=RuntimeError('injected native failure')):
                with self.assertRaisesRegex(RuntimeError,'injected native failure'):observer.observe(fixtures()[0])
            self.assertIs(sys.getprofile(),prior)
        finally:sys.setprofile(previous)

if __name__=='__main__':unittest.main()
