"""Declared native storage semantics before CUDA/Metal execution."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_healing_storage_cases import fixtures,negative_inputs
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L,FIELDS as F,check_schema
from world_projectile_native import observe


class HealingStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('storage_test_adapter',ROOT/'research/verify-world-healing-storage-short.py')
        cls.adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.adapter)
        cls.rows=fixtures();cls.native=[observe(c)[0] for c in cls.rows]

    def test_excess_storage_never_changes_maximum_hp(self):
        empty,filled=self.native[:2]
        self.assertEqual(empty['allies'][0]['max_hp'],filled['allies'][0]['max_hp'])
        self.assertEqual(filled['allies'][0]['hp']-empty['allies'][0]['hp'],2000)
        for i in (3,4):self.assertEqual(self.native[i]['allies'][0]['hp'],empty['allies'][0]['hp'])
        self.assertEqual(self.native[5]['allies'][0]['hp'],empty['allies'][0]['hp']-2000)

    def test_capacity_is_caster_snapshot_and_refresh_preserves_amount(self):
        cap=lambda i:self.native[i]['healing_storage'][0]['capacity'][0]
        self.assertEqual(cap(7),4000);self.assertEqual(cap(18),2000);self.assertEqual(cap(19),4000)
        self.assertEqual(cap(20),6000)
        self.assertEqual(self.native[13]['healing_storage'][0]['current'][0],730)

    def test_stable_activation_order_fill_and_spend_are_observed(self):
        self.assertEqual([r['current'][0] for r in self.native[15]['healing_storage']],[0,190])
        self.assertEqual([r['current'][0] for r in self.native[16]['healing_storage']],[2000,1730])

    def test_expiry_removal_repair_and_invincibility_keep_distinct_resources(self):
        self.assertEqual(self.native[12]['healing_storage'],[])
        self.assertEqual(self.native[17]['healing_storage'],[])
        self.assertEqual(self.native[25]['healing_storage'][0]['current'][0],2000)
        self.assertEqual(self.native[26]['healing_storage'][0]['current'][0],0)
        self.assertGreater(self.native[9]['healing_storage'][0]['current'][0],0)
        self.assertGreater(self.native[23]['allies'][0]['hp'],self.native[1]['allies'][0]['hp'])

    def test_negative_drain_uses_native_static_hp_synchronization_policy(self):
        for index,policy in [(11,1),(27,1),(28,0)]:
            words,_,_=self.adapter.suite.compile_case(self.rows[index])
            self.assertEqual(words[L['HP_UNCLAMP_POLICY']],policy)
        self.assertGreater(self.native[27]['allies'][0]['hp'],self.native[27]['allies'][0]['max_hp'])
        self.assertLessEqual(self.native[28]['allies'][0]['hp'],self.native[28]['allies'][0]['max_hp'])

    def test_canonical_stat_typed_object_and_private_boundary(self):
        before=copy.deepcopy(self.rows)
        for case in self.rows:
            words,_,_=self.adapter.suite.compile_case(case)
            for row,effect in enumerate(case['effects']):
                if effect.get('stat')!='heal_overcharge_store':continue
                self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['STAT']],74)
                self.assertEqual(words[L['PROTECTION_DEFINITION_BASE']+row],9)
                for options in ({},dict(combat={})):
                    with self.assertRaises(UnsupportedPortable):validate_effect(effect,**options)
                validate_effect(effect,combat={},world_frame=True)
        self.assertEqual(self.rows,before);check_schema()
        self.assertEqual(len(negative_inputs(self.adapter.suite.compile_case)),12)

    def test_periodic_static_conditions_and_refresh_use_native_clocks(self):
        by_name={c['name']:b for c,b in zip(self.rows,self.native)}
        ordinary=by_name['healing-storage-periodic-ordinary']
        self.assertEqual(ordinary,by_name['healing-storage-periodic-defender'])
        off=by_name['healing-storage-periodic-no-defender']
        self.assertGreater(ordinary['allies'][0]['hp'],off['allies'][0]['hp'])
        self.assertEqual(ordinary['allies'][0]['hp'],by_name['healing-storage-periodic-refresh']['allies'][0]['hp'])

    def test_cleanse_limit_and_scope_preserve_beneficial_storage(self):
        by_name={c['name']:b for c,b in zip(self.rows,self.native)}
        def carriers(label):return by_name['healing-storage-cleanse-'+label]['named_state']['allied_carriers']
        self.assertEqual([c['name'] for c in carriers('all-all')],['storage'])
        self.assertEqual([c['name'] for c in carriers('one-all')],['storage','harmful-second'])
        self.assertEqual(carriers('one-self')[1]['recipients'],[1,2,3,4])
        for label in ('all-all','one-all','one-self'):
            self.assertEqual(carriers(label)[0]['recipients'],list(range(5)))

    def test_overmax_heal_and_maxhp_grant_keep_distinct_storage_rules(self):
        by_name={c['name']:b for c,b in zip(self.rows,self.native)}
        for label in ('overmax-before-store-and-heal','maxhp-grant-does-not-fill'):
            b=by_name['healing-storage-'+label]
            self.assertEqual(b['healing_storage'][0]['current'],[0]*5)
        lazy=by_name['healing-storage-lazy-storage-with-lifesteal']['healing_storage'][0]
        self.assertEqual(lazy['recipients'],[4])


if __name__=='__main__':unittest.main()
