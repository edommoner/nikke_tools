"""Verify semantics before executing the shared CUDA/Metal case set."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_burst_recipient_cases import fixtures
from portable_runtime import validate_effect,UnsupportedPortable
from world_projectile_native import observe
from portable_specs import LIMITS as L,FIELDS as F


class BurstRecipientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=importlib.util.spec_from_file_location('burst_recipient_test',ROOT/'research/verify-world-burst-recipients-short.py')
        cls.adapter=importlib.util.module_from_spec(s);s.loader.exec_module(cls.adapter)
        cls.rows=fixtures();cls.native=[observe(c)[0] for c in cls.rows]

    def test_reentry_is_caster_owned_even_when_authored_all_allies(self):
        baseline,self_only,allies,two=self.native[:4]
        self.assertEqual(self_only,allies)
        self.assertEqual(allies,two)  # second caster cannot reopen the same stage
        self.assertEqual(baseline['manual_control']['burst_users'],[1,4,8])
        self.assertEqual(allies['manual_control']['burst_users'],[3,4,8])
        self.assertNotEqual(baseline['damage'],allies['damage'])
        self.assertEqual(allies,self.native[6])  # native reenters the current stage

    def test_instant_names_absence_order_and_colon_names_have_observable_health(self):
        hp=lambda i:[a['hp'] for a in self.native[i]['allies']]
        self.assertEqual(hp(7),[5000]*4+[6000]);self.assertEqual(hp(8),[5000]*5)
        self.assertEqual(hp(9),[6000]*4+[7000]);self.assertEqual(hp(10),hp(7))
        self.assertEqual(hp(11),[5000]*5);self.assertEqual(hp(12),[5000,5000,6000,5000,5000])

    def test_programs_pack_without_mutation_and_reentry_does_not_gain_other_targets(self):
        before=copy.deepcopy(self.rows)
        for c in self.rows:self.adapter.suite.compile_case(c)
        self.assertEqual(self.rows,before)
        effect=self.rows[2]['effects'][1]
        for target in ('boss','all_allies_excl_self','N102'):
            with self.assertRaises(UnsupportedPortable):validate_effect(dict(effect,target=target),combat={})
        with self.assertRaises(UnsupportedPortable):validate_effect(effect)
        words,_,_=self.adapter.suite.compile_case(self.rows[2])
        self.assertEqual(words[L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['KIND']],25)

    def test_invalid_reentry_value_is_rejected_before_packing(self):
        for value in (0,float('nan'),float('inf'),None,True):
            with self.subTest(value=value),self.assertRaises(UnsupportedPortable):
                validate_effect(dict(self.rows[2]['effects'][1],fixed_value=value),combat={})

    def test_gpu_negative_cases_are_distinct_literal_mutations(self):
        from portable_burst_recipient_cases import negative_inputs
        seed=self.adapter.suite.compile_case(self.rows[2])[0]
        bad=negative_inputs(self.adapter.suite.compile_case)
        self.assertEqual(len(bad),6)
        for name,raw,domain in bad:
            self.assertIsNone(domain);self.assertEqual(sum(a!=b for a,b in zip(seed,raw)),1)


if __name__=='__main__':unittest.main()
