"""Native semantics, exact source delta and conservative event admission."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_ally_burst_cases import fixtures
from portable_ally_burst_contracts import verify
import world_ally_burst_native as observer
from world_projectile_native import observe as plain_observe
from portable_trigger_specs import validate_input,UnsupportedTrigger
from portable_definition_view_contract import verify as source_verify
import portable_backend,portable_runtime,detail_gpu

class AllyBurstTests(unittest.TestCase):
    def test_literal_native_contracts_without_gpu_or_packing(self):
        stop=lambda *a,**kw: (_ for _ in ()).throw(AssertionError('Forbidden GPU/packing'))
        cases=fixtures();before=copy.deepcopy(cases)
        with patch.object(portable_backend,'build',stop),patch.object(portable_backend,'execute',stop),patch.object(portable_runtime,'compile_program',stop),patch.object(detail_gpu,'compile_effects',stop):
            for case in cases:
                with self.subTest(case=case['name']):
                    native,_=observer.observe(case);self.assertTrue(verify(case,native)['verified'])
        self.assertEqual(cases,before)
    def test_observer_retains_every_battle_field_and_trace(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                expected,trace=plain_observe(case);actual,observed=observer.observe(case)
                actual.pop('ally_burst_events');self.assertEqual(actual,expected);self.assertEqual(observed,trace)
    def test_notice_order_owner_missing_cast_and_health_faults_fail(self):
        case=fixtures()[1];native,_=observer.observe(case)
        for kind in ('order','owner','cast','activation','health'):
            changed=copy.deepcopy(native);events=changed['ally_burst_events']
            if kind=='order':events[2],events[3]=events[3],events[2]
            elif kind=='owner':events[2]['owner']=1
            elif kind=='cast':events.pop(0)
            elif kind=='activation':events.pop(next(i for i,e in enumerate(events) if e['kind']=='activate'))
            else:changed['allies'][0]['hp']+=1
            with self.subTest(kind=kind),self.assertRaises(AssertionError):verify(case,changed)
    def test_profile_restored_on_failure_and_composed_with_prior(self):
        calls=[];prior=sys.getprofile()
        def profile(frame,event,value):
            if event=='call' and frame.f_code is observer.BuffManager.notify.__code__:calls.append(event)
        try:
            sys.setprofile(profile);observer.observe(fixtures()[1]);self.assertTrue(calls);self.assertIs(sys.getprofile(),profile)
            with patch.object(observer,'native_observe',side_effect=RuntimeError('injected')):
                with self.assertRaisesRegex(RuntimeError,'injected'):observer.observe(fixtures()[1])
            self.assertIs(sys.getprofile(),profile)
        finally:sys.setprofile(prior)
    def test_broadcast42_and_caster_stage41_remain_private_world_only(self):
        effect=fixtures()[1]['effects'][-1]
        validate_input(effect,world_frame=True)
        with self.assertRaises(UnsupportedTrigger):validate_input(effect)
        for timing in ('squad_burst_cast:1','squad_burst_cast:2','squad_burst_cast:3'):
            staged=copy.deepcopy(effect);staged['trigger']['timing']=[timing]
            validate_input(staged,world_frame=True)
            with self.assertRaises(UnsupportedTrigger):validate_input(staged,world_frame=False)
    def test_source_delta_rejects_order_omission_owner_and_admission_mutations(self):
        self.assertEqual(set(source_verify(ROOT)['reviewed_ally_burst_sources']),{'gpu/combat_runtime.slang','gpu/admission_runtime.slang'})
        for name,old,new in [('gpu/combat_runtime.slang','nextEventCandidate(s,42,0)','nextEventCandidate(s,41,0)'),('gpu/combat_runtime.slang','dispatch(s,0,42,who,0,when,output)','dispatch(s,0,42,picked,0,when,output)'),('gpu/combat_runtime.slang','who = 0; who < 5 &&','who = 1; who < 5 &&'),('gpu/admission_runtime.slang','event == 42 && s.combat == 0','event == 41 && s.combat == 0')]:
            text=(ROOT/name).read_text();self.assertIn(old,text)
            with self.subTest(name=name,old=old),self.assertRaises(AssertionError):source_verify(ROOT,sources={name:text.replace(old,new,1)})
    def test_shared_adapter_packs_literal_cases_and_one_rejection(self):
        spec=importlib.util.spec_from_file_location('ally_burst_test_adapter',ROOT/'research/verify-world-ally-burst-short.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        entries,data=m.prepare();self.assertEqual(len(entries),16);self.assertEqual(len(data),4+16*m.suite.INPUT*4)
        self.assertEqual(entries[-1][0],'reject/ally-burst-no-combat');self.assertIsNone(entries[-1][2])

if __name__=='__main__':unittest.main()
