"""Native effective defense, strict ordering, lazy/eager and source boundaries."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend,portable_runtime,detail_gpu
from calculator.buff_manager import BuffManager
from portable_below_def_cases import fixtures
from portable_below_def_contracts import verify
from world_below_def_native import observe
from world_projectile_native import observe as plain
from portable_below_def_source_contract import project_sources

def adapter():
    s=importlib.util.spec_from_file_location('below_def_test',ROOT/'research/verify-world-below-def-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class BelowDefenseTests(unittest.TestCase):
    def test13_literal_contracts_without_compilation_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases)
        def no(*a,**k):raise AssertionError('Compilation/GPU forbidden')
        with patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no),patch.object(portable_runtime,'compile_program',no),patch.object(detail_gpu,'compile_effects',no):
            for c in cases:
                with self.subTest(case=c['name']):n,_=observe(c);self.assertTrue(verify(c,n)['verified'])
        self.assertEqual(cases,before)
    def test_observation_preserves_battle_trace_and_all_existing_queries(self):
        for c in fixtures():
            def measured(fn):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'_effective_def',autospec=True,side_effect=BuffManager._effective_def) as defense,patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=fn(c);return result,(get.call_count,defense.call_count,sample.call_count)
            with self.subTest(case=c['name']):
                (n,t),reads=measured(observe);n.pop('below_def_selections');(old,trace),counts=measured(plain);self.assertEqual((n,t),(old,trace));self.assertEqual(reads,counts)
    def test_wrong_comparison_order_owner_lazy_and_dead_target_reject(self):
        c=fixtures()[0];n,_=observe(c)
        for fault in ('equal','order','owner','lazy','dead','count'):
            bad=copy.deepcopy(n);rows=bad['below_def_selections'];row=rows[0]
            if fault=='equal':row['reads'][3]['value']=100
            elif fault=='order':row['reads'].reverse()
            elif fault=='owner':row['owner']=4
            elif fault=='lazy':row['lazy']=False
            elif fault=='dead':row['picked']=[0]
            else:rows.pop()
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,bad)
    def test_all21_wire_inputs_and_rejection_none_domains(self):
        m=adapter();rows,data=m.prepare();self.assertEqual(len(rows),21);self.assertEqual(sum(d is None for _,_,d in rows),8);self.assertEqual(len(data),4+21*104400*4)
        for name,_,d in rows[13:]:self.assertIsNone(d);m.validate_rejection([64],name)
        for combat,world in ((None,True),({},False)):
            with self.assertRaises(portable_runtime.UnsupportedPortable):portable_runtime.validate_effect(fixtures()[0]['effects'][1],combat=combat,world_frame=world)
    def test_shared_combiner_keeps23_rejection_domains_and95_strides(self):
        s=importlib.util.spec_from_file_location('below_retention_test',ROOT/'research/verify-world-below-def-retention-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        rows,data=m.prepare();self.assertEqual(len(rows),95);self.assertEqual(sum(d is None for _,_,d in rows),23);self.assertEqual(len(data),4+95*104400*4)
        for name,_,domain in rows:
            if domain is None:m.validate_rejection([64],name)

    def test_source_ledger_rejects_base_only_non_strict_wrong_caster_and_scope(self):
        project_sources(ROOT)
        name='gpu/below_def_recipient_runtime.slang';s=(ROOT/name).read_text()
        for before,after in [('f64Less(value,threshold)','!f64Less(threshold,value)'),('scalarValue(s,slot,d.owner)','scalarValue(s,slot,who)'),('s.lazyPending[slot]!=0','false'),('s.baseDefense[who]','s.baseDefense[owner]'),('f64Div(percent,HUNDRED)','f64Div(percent,ONE)')]:
            self.assertIn(before,s)
            with self.subTest(before=before),self.assertRaises(AssertionError):project_sources(ROOT,{name:s.replace(before,after,1)})
        n='gpu/recipient_runtime.slang';s=(ROOT/n).read_text()
        with self.assertRaises(AssertionError):project_sources(ROOT,{n:s.replace('#ifdef PORTABLE_BELOW_DEF','#if 1',1)})

if __name__=='__main__':unittest.main()
