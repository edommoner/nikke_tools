"""Named capacity model stays explicit and retains the ordinary compiler gate."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_effect_target_count_shared_cases import fixtures,native,query
from portable_effect_target_count_specs import compile_program,STAT
from effect_target_count_policy import MODEL
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import compile_program as ordinary,UnsupportedPortable
from test_target_counter_runtime import NAMES
import engine_worker

class NamedCapacityGPUContractTests(unittest.TestCase):
    def setUp(self):
        self.chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
        self.case=fixtures()[0]
    def compile(self,case=None,model=MODEL):
        c=case or self.case
        return compile_program(self.chars,list(zip(c['effects'],[NAMES[i] for i in c['owners']])),c['script'],[1000]*5,model=model)
    def test_native_cases_prove_expiry_stacks_name_and_recipient_lifetimes(self):
        expected=[[15,15,5],[15,5],[15,25,35,5],[15,8,5],[15,15],[15,5]]
        for c,want in zip(fixtures(),expected,strict=True):
            with self.subTest(name=c['name']):self.assertEqual([q['capacity'] for q in native(c)['queries']],want)
    def test_static_lowering_has_no_battle_queries_and_does_not_mutate_source(self):
        from unittest.mock import patch
        from calculator import timeline
        import portable_backend
        before=copy.deepcopy((self.chars,self.case))
        def forbidden(*a,**kw):raise AssertionError('Calculation during static lowering')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):w,m=self.compile()
        self.assertEqual((self.chars,self.case),before);self.assertEqual(w[L['DEFINITION_BASE']+F['STAT']],STAT)
        self.assertEqual(w[L['DEFINITION_BASE']+F['TARGET_NAME']],m['states']['록 온'])
        self.assertFalse(m['named_target_count']['physical_shot_lifetime_verified']);self.assertFalse(m['named_target_count']['full_profile_verified'])
    def test_default_admission_and_physical_shot_duration_remain_closed(self):
        with self.assertRaises(UnsupportedPortable):ordinary(self.chars,[(self.case['effects'][0],NAMES[0])],[[0,0,0,0,0,-1,0,0]],[1000]*5)
        c=copy.deepcopy(self.case);c['effects'][0]['duration_bullets']=2
        with self.assertRaisesRegex(ValueError,'physical battle'):self.compile(c)
        with self.assertRaisesRegex(ValueError,'Explicit'):self.compile(model='implicit')
    def test_bad_query_capacity_duplicate_indices_and_unknown_fields_fail(self):
        for mutation in ({'who':True},{'index':True},{'capacity_limit':4},{'base_count':.5},{'time':float('nan')},{'extra':0}):
            c=copy.deepcopy(self.case);c['script'][1].update(mutation)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.compile(c)
        c=copy.deepcopy(self.case);c['script'][2]['index']=0
        with self.assertRaises(ValueError):self.compile(c)
    def test_adapter_has_six_native_and_three_device_admission_negatives(self):
        spec=importlib.util.spec_from_file_location('capacity_adapter_test',ROOT/'research/verify-named-target-count-query.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        entries,data=adapter.prepare();self.assertEqual(len(entries),9);self.assertEqual(sum(d is not None for _,_,d in entries),6)
        self.assertEqual(len(data),(1+9*L['INPUT_WORDS'])*4)

if __name__=='__main__':unittest.main()
