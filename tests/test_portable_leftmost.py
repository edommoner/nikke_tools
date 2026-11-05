"""Live-before-limit selection, observation fidelity and strict wire boundaries."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend,portable_runtime,detail_gpu
from calculator.buff_manager import BuffManager
from portable_leftmost_cases import fixtures
from portable_leftmost_contracts import verify
from world_leftmost_native import observe
from world_projectile_native import observe as plain
from portable_recipient_specs import admitted
from portable_specs import LIMITS as L

def adapter():
    s=importlib.util.spec_from_file_location('leftmost_test',ROOT/'research/verify-world-leftmost-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class LeftmostTests(unittest.TestCase):
    def test13_literal_native_contracts_without_packing_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases)
        def no(*a,**k):raise AssertionError('GPU/packing forbidden')
        with patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no),patch.object(portable_runtime,'compile_program',no),patch.object(detail_gpu,'compile_effects',no):
            for c in cases:
                with self.subTest(case=c['name']):n,_=observe(c);self.assertTrue(verify(c,n)['verified'])
        self.assertEqual(cases,before)
    def test_observer_preserves_battle_trace_and_semantic_reads(self):
        for c in fixtures():
            def run(fn):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'_resolve_target',autospec=True,side_effect=BuffManager._resolve_target) as resolve,patch.object(random,'sample',side_effect=random.sample) as sample:
                    data=fn(c);return data,(get.call_count,resolve.call_count,sample.call_count)
            with self.subTest(case=c['name']):
                (n,t),reads=run(observe);n.pop('leftmost_selections');(old,trace),counts=run(plain)
                self.assertEqual((n,t),(old,trace));self.assertEqual(reads,counts)
    def test_wrong_count_owner_order_and_dead_selection_reject(self):
        c=next(c for c in fixtures() if c['name']=='leftmost-death-between-activations');n,_=observe(c)
        for fault in ('count','owner','order','dead','target','orphan'):
            bad=copy.deepcopy(n);rows=bad['leftmost_selections']
            if fault=='count':rows.pop()
            elif fault=='owner':rows[0]['owner']=4
            elif fault=='order':rows[0]['picked'].reverse()
            elif fault=='dead':rows[1]['picked']=[0,1]
            elif fault=='target':rows[0]['target']='all_allies'
            else:rows.append(copy.deepcopy(rows[0]))
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,bad)
    def test_death_and_instant_witnesses_are_observable_in_final_state(self):
        cases={c['name']:c for c in fixtures()}
        n,_=observe(cases['leftmost-death-between-activations'])
        self.assertGreater(n['allies'][2]['defense'],100)
        n,_=observe(cases['leftmost-instant-after-death'])
        self.assertEqual([a['hp'] for a in n['allies']],[8000,0,7000,5000,5000])
    def test_strict_admission_and21_shared_wire_cases(self):
        for suffix in ('0','1','5'):self.assertTrue(admitted('allies_code_weapon_leftmost:작열:AR:'+suffix))
        for target in ('allies_code_weapon_leftmost:작열:AR:6','allies_code_weapon_leftmost:작열:AR:-1','allies_code_weapon_leftmost:작열:AR:01','allies_code_weapon_leftmost::AR:1','allies_code_weapon_leftmost:작열:AR:１','allies_code_weapon_leftmost:작열:AR:1:'):
            self.assertFalse(admitted(target),target)
        m=adapter();rows,data=m.prepare();self.assertEqual(len(rows),21);self.assertEqual(len(data),4+21*m.suite.INPUT*4)
        for _,w,d in rows[:13]:self.assertTrue(any(w[L['RECIPIENT_BASE']+i*8]==24 for i in range(w[1])))
        for name,_,d in rows[13:]:self.assertIsNone(d);m.validate_rejection([64],name)
    def test_exact_delta_rejects_gate_order_mask_count_and_arithmetic_edits(self):
        from portable_leftmost_source_contract import project_sources
        sources,_=project_sources(ROOT)
        import hashlib,json
        ledger=json.loads((ROOT/'tests/fixtures/portable-leftmost-source-delta.json').read_text())
        self.assertEqual(hashlib.sha256(sources['gpu/recipient_runtime.slang'].encode()).hexdigest(),ledger['sources']['gpu/recipient_runtime.slang']['baseline_sha256'])
        original=(ROOT/'gpu/recipient_runtime.slang').read_text()
        for before,after in [('written<count','written<=count'),('s.downMask&(1U<<who)','s.downMask&(1U<<d.owner)'),('#ifdef PORTABLE_LEFTMOST','#if 1'),('count<=5','count<=6'),('kind == 0','kind == 1')]:
            self.assertIn(before,original)
            with self.subTest(before=before),self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/recipient_runtime.slang':original.replace(before,after,1)})

    def test_comparison_rejects_wrong_recipient_defense_and_instant_hp(self):
        m=adapter()
        for c,key in [(fixtures()[0],'defense'),(next(c for c in fixtures() if c['name']=='leftmost-instant-after-death'),'hp')]:
            expected=m.native_reference((c,None,None));actual=copy.deepcopy(expected['battle']);actual['allies'][1][key]+=10
            with self.subTest(key=key),patch.object(m,'native_reference',return_value=expected),patch.object(m.suite,'decoded',return_value=actual),patch.object(m.base.base.storage,'decoded_storage',return_value=expected['battle']['healing_storage']) as storage,self.assertRaises(AssertionError):m.compare([0],(c,None,None))
            storage.assert_called_once()

if __name__=='__main__':unittest.main()
