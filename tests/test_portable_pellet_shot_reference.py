"""Per-shot native contracts must pass before any shared GPU admission."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from portable_pellet_shot_cases import fixtures
from portable_pellet_shot_contracts import verify
import world_pellet_shot_native as observer
spec=importlib.util.spec_from_file_location('pellet_shot_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class PelletShotReferenceTests(unittest.TestCase):
    def test_twenty_one_literal_contracts_without_packing_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),21)
        def forbidden(*a,**kw):raise AssertionError('packing/GPU forbidden')
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observer.observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_observer_preserves_every_native_field_and_trace(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                plain,trace=observer.projectile_observe(case);observed,otrace=observer.observe(case)
                observed.pop('pellet_shot');self.assertEqual(observed,plain);self.assertEqual(otrace,trace)

    def test_notification_identity_order_count_owner_time_and_damage_faults_reject(self):
        case=next(c for c in fixtures() if c['name'].endswith('raw-aliases'));native,_=observer.observe(case)
        for fault in ('raw','order','count','owner','time','missing-notice','extra-notice','stack','extra-stack','packet-damage','packet-count','packet-missing','total','event-order','event-missing'):
            altered=copy.deepcopy(native);obs=altered['pellet_shot']
            if fault=='raw':obs['notices'][0]['raw']='5'
            elif fault=='order':obs['notices'][0],obs['notices'][1]=obs['notices'][1],obs['notices'][0]
            elif fault in ('count','owner','time'):obs['notices'][0][fault]+=1
            elif fault=='missing-notice':obs['notices'].pop()
            elif fault=='extra-notice':obs['notices'].append(copy.deepcopy(obs['notices'][0]))
            elif fault=='stack':obs['stacks']['shot-watch']-=1
            elif fault=='extra-stack':obs['stacks']['shot-watch-unexpected']=1
            elif fault=='packet-damage':altered['projectile_shots'][0]['damage']+=1
            elif fault=='packet-count':altered['projectile_shots'][0]['pellets']+=1
            elif fault=='packet-missing':altered['projectile_shots'].pop()
            elif fault=='total':altered['damage'][0]+=1
            elif fault=='event-order':obs['events'][0],obs['events'][5]=obs['events'][5],obs['events'][0]
            elif fault=='event-missing':obs['events'].pop()
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,altered)

    def test_single_notice_preserves_duplicate_activations_and_captured_split(self):
        cases={c['name']:c for c in fixtures()}
        for label in ('duplicate-descriptor','captured-count','charge-does-not-notify','expiry','last-owner'):
            case=cases['pellet-shot-'+label];native,_=observer.observe(case)
            self.assertTrue(verify(case,native)['verified'])
            native['pellet_shot']['stacks']['shot-watch']=999
            with self.subTest(case=label),self.assertRaises(AssertionError):verify(case,native)

    def test_composes_and_restores_profile_on_success_and_failure(self):
        previous=sys.getprofile();calls=[]
        def prior(frame,event,answer):
            if event=='call' and frame.f_code is observer.BuffManager.notify.__code__:calls.append(event)
        try:
            sys.setprofile(prior);observer.observe(fixtures()[0]);self.assertTrue(calls);self.assertIs(sys.getprofile(),prior)
            with patch.object(observer,'projectile_observe',side_effect=RuntimeError('injected failure')):
                with self.assertRaisesRegex(RuntimeError,'injected failure'):observer.observe(fixtures()[0])
            self.assertIs(sys.getprofile(),prior)
        finally:sys.setprofile(previous)

    def test_native_stage_stays_separate_from_gpu_evidence(self):
        from portable_reference import REFERENCES
        self.assertEqual(REFERENCES['pellet-shot'],('portable_pellet_shot_cases','world_pellet_shot_native','portable_pellet_shot_contracts'))
        self.assertEqual(cli.SUITES['pellet-shot']['native'],21)

    def test_observation_adds_no_buff_queries(self):
        code=observer.BuffManager.get_buffs.__code__;previous=sys.getprofile()
        def count_queries(run):
            calls=[]
            def profile(frame,event,answer):
                if event=='call' and frame.f_code is code:
                    calls.append((frame.f_locals['caster'],frame.f_locals['t']))
            sys.setprofile(profile)
            try:run()
            finally:sys.setprofile(previous)
            return calls
        for case in fixtures():
            with self.subTest(case=case['name']):
                self.assertEqual(count_queries(lambda:observer.projectile_observe(case)),count_queries(lambda:observer.observe(case)))


if __name__=='__main__':unittest.main()
