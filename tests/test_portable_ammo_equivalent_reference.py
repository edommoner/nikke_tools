"""Literal native ammo-equivalent contracts; packing and GPU remain forbidden."""
import copy,importlib.util,inspect,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from portable_ammo_equivalent_cases import fixtures
from portable_ammo_equivalent_contracts import verify
import world_ammo_equivalent_native as observer
spec=importlib.util.spec_from_file_location('ammo_equivalent_reference_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class AmmoEquivalentReferenceTests(unittest.TestCase):
    def test_exact_catalogue_effect_fires_40_notices_per_charged_shot(self):
        from portable_ammo_equivalent_catalogue_cases import fixtures as catalogue_fixtures
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('Packing forbidden')):
            case=catalogue_fixtures()[0];native,trace=observer.observe(case)
            self.assertTrue(verify(case,native)['verified']);self.assertEqual(native['ammo_equivalent']['squad_count'],80)
            self.assertEqual(native['ammo'][0],8);native.pop('ammo_equivalent')
            plain,ptrace=observer.projectile_observe(case);self.assertEqual(native,plain);self.assertEqual(trace,ptrace)
    def test_actor_pool_geometry_true_false_native_contracts(self):
        from portable_ammo_equivalent_geometry_cases import fixtures as geometry_fixtures
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('Packing forbidden')):
            for case in geometry_fixtures():
                with self.subTest(case=case['name']):
                    native,trace=observer.observe(case);self.assertTrue(verify(case,native)['verified'])
                    native.pop('ammo_equivalent');plain,ptrace=observer.projectile_observe(case)
                    self.assertEqual(native,plain);self.assertEqual(trace,ptrace)
    def test_twenty_five_literal_contracts_without_packing_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),25)
        def forbidden(*a,**kw):raise AssertionError('packing/GPU forbidden')
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observer.observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_every_native_field_and_trace_is_preserved(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                plain,trace=observer.projectile_observe(case);observed,otrace=observer.observe(case);observed.pop('ammo_equivalent')
                self.assertEqual(observed,plain);self.assertEqual(otrace,trace)

    def test_faults_in_counts_ownership_order_ticks_damage_and_ammo_reject(self):
        case=fixtures()[0];native,_=observer.observe(case)
        for fault in ('count','squad-count','notice-owner','notice-time','origin','origin-order','call-count','call-name','call-value','call-owner','call-time','tick','stack','stack-owner','damage','packet-count','total','ammo'):
            altered=copy.deepcopy(native);obs=altered['ammo_equivalent']
            if fault=='count':obs['notices'].pop()
            elif fault=='squad-count':obs['squad_count']+=1
            elif fault=='notice-owner':obs['notices'][0]['owner']=1
            elif fault=='notice-time':obs['notices'][0]['time']=999
            elif fault=='origin':obs['notices'][0]['origin']='invented'
            elif fault=='origin-order':obs['notices'][0]['origin'],obs['notices'][1]['origin']=obs['notices'][1]['origin'],obs['notices'][0]['origin']
            elif fault=='call-count':obs['calls'].pop()
            elif fault=='call-name':obs['calls'][0]['name']='invented'
            elif fault=='call-value':obs['calls'][0]['value']+=1
            elif fault=='call-owner':obs['calls'][0]['owner']=1
            elif fault=='call-time':obs['calls'][0]['time']=999
            elif fault=='tick':obs['calls'][0]['from_tick']=True
            elif fault=='stack':obs['stacks'][0]['stack']+=1
            elif fault=='stack-owner':obs['stacks'][0]['owner']=1
            elif fault=='damage':altered['projectile_shots'][0]['damage']+=1
            elif fault=='packet-count':altered['projectile_shots'][0]['muzzles']+=1
            elif fault=='total':altered['damage'][0]+=1
            elif fault=='ammo':altered['ammo'][0]-=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,altered)

    def test_recursion_budget_and_periodic_phase_faults_reject(self):
        for case in fixtures():
            if not any(case['name'].endswith(label) for label in ('recursive-bounded','recursive-once','periodic','infinite-ammo','cross-owner-global-counter','charge-every-notice','maximum')):continue
            native,_=observer.observe(case);self.assertTrue(verify(case,native)['verified'])
            native['ammo_equivalent']['notices'][0]['origin']='physical' if case['name'].endswith('infinite-ammo') else 'equivalent'
            with self.subTest(case=case['name']),self.assertRaises(AssertionError):verify(case,native)

    def test_profile_composes_and_restores_after_success_and_failure(self):
        previous=sys.getprofile();calls=[];code=inspect.unwrap(observer.BuffManager._dispatch_instant).__code__
        def prior(frame,event,answer):
            if event=='call' and frame.f_code is code:calls.append(event)
        try:
            sys.setprofile(prior);observer.observe(fixtures()[0]);self.assertTrue(calls);self.assertIs(sys.getprofile(),prior)
            with patch.object(observer,'projectile_observe',side_effect=RuntimeError('injected failure')):
                with self.assertRaisesRegex(RuntimeError,'injected failure'):observer.observe(fixtures()[0])
            self.assertIs(sys.getprofile(),prior)
            for value,error in ((float('nan'),ValueError),(float('inf'),OverflowError)):
                case=fixtures()[0];case['effects'][1]['fixed_value']=value
                with self.subTest(value=value),self.assertRaises(error):observer.observe(case)
                self.assertIs(sys.getprofile(),prior)
        finally:sys.setprofile(previous)

    def test_observation_adds_no_buff_queries(self):
        code=observer.BuffManager.get_buffs.__code__;previous=sys.getprofile()
        def count_queries(run):
            calls=[]
            def profile(frame,event,answer):
                if event=='call' and frame.f_code is code:calls.append((frame.f_locals['caster'],frame.f_locals['t']))
            sys.setprofile(profile)
            try:run()
            finally:sys.setprofile(previous)
            return calls
        for case in fixtures():
            with self.subTest(case=case['name']):self.assertEqual(count_queries(lambda:observer.projectile_observe(case)),count_queries(lambda:observer.observe(case)))

    def test_native_stage_registration_is_separate_from_gpu_evidence(self):
        from portable_reference import REFERENCES
        self.assertEqual(REFERENCES['ammo-equivalent'],('portable_ammo_equivalent_cases','world_ammo_equivalent_native','portable_ammo_equivalent_contracts'))
        self.assertEqual(cli.SUITES['ammo-equivalent']['native'],29)
        with self.assertRaises(portable_runtime.UnsupportedPortable):portable_runtime.validate_effect(dict(fixtures()[0]['effects'][1],scaling='stack_count'),combat={},world_frame=True)


if __name__=='__main__':unittest.main()
