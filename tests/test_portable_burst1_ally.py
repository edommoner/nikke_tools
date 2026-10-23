"""Self exclusion, live stage lifetime, down actors and guarded GPU admission."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend,portable_runtime,detail_gpu
from calculator.buff_manager import BuffManager
from portable_burst1_ally_cases import fixtures
from world_burst1_ally_native import observe
from world_projectile_native import observe as plain
from portable_burst1_ally_contracts import verify
from portable_burst1_ally_source_contract import project_sources

def adapter(name='burst1-ally'):
    s=importlib.util.spec_from_file_location('burst1_test_'+name,ROOT/'research'/('verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class Burst1AllyTests(unittest.TestCase):
    def test12_literal_contracts_without_compilation_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases)
        def no(*a,**k):raise AssertionError('Compilation/GPU forbidden')
        with patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no),patch.object(portable_runtime,'compile_program',no),patch.object(detail_gpu,'compile_effects',no):
            for c in cases:
                with self.subTest(case=c['name']):n,_=observe(c);self.assertTrue(verify(c,n)['verified'])
        self.assertEqual(cases,before)
    def test_observation_preserves_battle_trace_and_condition_value_rng_calls(self):
        for c in fixtures():
            def measured(fn):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'_condition_ok',autospec=True,side_effect=BuffManager._condition_ok) as condition,patch.object(BuffManager,'_get_value',autospec=True,side_effect=BuffManager._get_value) as value,patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=fn(c);return result,(get.call_count,condition.call_count,value.call_count,sample.call_count)
            with self.subTest(case=c['name']):
                (n,t),reads=measured(observe);n.pop('burst1_ally_conditions');(old,trace),counts=measured(plain);self.assertEqual((n,t),(old,trace));self.assertEqual(reads,counts)
    def test_wrong_result_self_inclusion_stage_lifetime_down_and_hp_reject(self):
        cases=fixtures();c=cases[4];n,_=observe(c)
        for fault in ('result','owner','stage','count','hp'):
            bad=copy.deepcopy(n);r=bad['burst1_ally_conditions']
            if fault=='result':r[0]['result']=False
            elif fault=='owner':r[0]['owner']=1
            elif fault=='stage':r[1]['stages'][1]='1'
            elif fault=='count':r.pop()
            else:bad['allies'][0]['hp']+=100
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,bad)
        c=cases[3];n,_=observe(c);n['burst1_ally_conditions'][1]['down']=[]
        with self.assertRaises(AssertionError):verify(c,n)
    def test20_wire_inputs_and_typed_rejections_preserve_none_domains(self):
        m=adapter();rows,data=m.prepare();self.assertEqual(len(rows),20);self.assertEqual(sum(d is None for _,_,d in rows),8);self.assertEqual(len(data),4+20*104400*4)
        for name,_,domain in rows[12:]:self.assertIsNone(domain);m.validate_rejection([64],name)
    def test_combiner_has125_inputs_and31_rejections(self):
        m=adapter('burst1-ally-retention');rows,data=m.prepare();self.assertEqual(len(rows),125);self.assertEqual(sum(d is None for _,_,d in rows),31);self.assertEqual(len(data),4+125*104400*4)
        for name,_,d in rows:
            if d is None:m.validate_rejection([64],name)
    def test_exact_source_delta_rejects_weakened_guards_or_evaluator_changes(self):
        project_sources(ROOT);name='gpu/world_actor_fields.slang';s=(ROOT/name).read_text()
        for before,after in [('s.combat==0 || commands[at+1]!=0 || !f64Zero(arg)','false'),('kind==C_BURST1_ALLY || kind==C_NO_BURST1_ALLY','kind==C_NO_BURST1_ALLY'),('#ifdef PORTABLE_BURST1_ALLY','#if 1')]:
            self.assertIn(before,s)
            with self.subTest(before=before),self.assertRaises(AssertionError):project_sources(ROOT,{name:s.replace(before,after,1)})
        from portable_definition_view_contract import verify as verify_all
        text=(ROOT/'gpu/event_runtime.slang').read_text();before='who != owner && s.currentStage[who] == 1';self.assertIn(before,text)
        with self.assertRaises(AssertionError):verify_all(ROOT,sources={'gpu/event_runtime.slang':text.replace(before,'s.currentStage[who] == 1',1)})

if __name__=='__main__':unittest.main()
