"""Native lifetime contracts, final scalar observation and exact source containment."""
import copy,importlib.util,json,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime
from portable_heal_charge_lifetime_cases import fixtures
from portable_heal_charge_lifetime_contracts import verify
from world_heal_charge_native import observe_extended,plain
from portable_specs import LIMITS as L
from portable_heal_charge_observation import compare_final

def adapter():
    s=importlib.util.spec_from_file_location('lifetime_test_adapter',ROOT/'research/verify-world-heal-charge-lifetime-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class HealingChargeLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.answers=[observe_extended(c) for c in cls.cases]
    def test_literal_retained_removed_persistent_and_shared_owner_cases(self):
        self.assertEqual(len(self.cases),12)
        for c,(n,t) in zip(self.cases,self.answers):
            with self.subTest(case=c['name']):verify(c,n)
    def test_complete_native_battle_trace_and_rng_unchanged(self):
        for c,(n,t) in zip(self.cases,self.answers):
            bare=copy.deepcopy(n);bare.pop('healing_charge')
            with self.subTest(case=c['name']):self.assertEqual((bare,t),plain(c))
    def test_factory_never_runs_a_battle_or_packs_gpu_quantities(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle')),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No GPU packing')):self.assertEqual(fixtures(),self.cases)
    def test_final_state_observer_rejects_hidden_amount_flags_and_membership(self):
        c=self.cases[7];n=self.answers[7][0];w,meta,b=adapter().suite.compile_case(c);words=[0]*L['WORLD_RELOAD_OUTPUT_WORDS'];words[9]=1
        at=L['CARRIER_STATE_BASE'];words[at]=1;words[at+1]=1;words[at+4]=1;words[at+9]=1
        obj=L['PROTECTION_OBJECT_BASE'];words[L['PROTECTION_MAP_BASE']+1]=1
        words[obj+4]=meta['states']['pool'];words[obj+20]=1;words[obj+21]=1;words[obj+22]=10
        words[obj:obj+2]=struct.unpack('<II',struct.pack('<d',1000.));words[obj+2:obj+4]=struct.unpack('<II',struct.pack('<d',1500.))
        compare_final(words,meta,c,n['healing_charge'])
        for offset in (obj+1,obj+22,at+4):
            wrong=list(words);wrong[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(AssertionError):compare_final(wrong,meta,c,n['healing_charge'])
    def test_new_cases_pack_without_cpu_charge_values(self):
        rows,_=adapter().prepare();self.assertEqual(len(rows),12)
        for name,w,domain in rows:self.assertEqual(w[L['PROTECTION_META_BASE']]&64,64)
    def test_new_source_delta_is_reversible_and_rejects_unreviewed_edits(self):
        from portable_heal_charge_lifetime_source_contract import project_sources
        d=json.loads((ROOT/'tests/fixtures/portable-heal-charge-lifetime-source-delta.json').read_text());result=project_sources(ROOT)
        for name,row in d['sources'].items():
            self.assertEqual(result[name],row['baseline'])
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n'})
    def test_final_native_lifetime_contract_rejects_hidden_stale_pool(self):
        c=self.cases[9];n=copy.deepcopy(self.answers[9][0]);n['healing_charge']['final']=[dict(row=1,current=1000,active=False,ended=True)]
        with self.assertRaises(AssertionError):verify(c,n)
if __name__=='__main__':unittest.main()
