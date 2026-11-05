import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import LIMITS as L
from portable_runtime_layout import runtime_initializer


class BurstChargeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('burst_charge_core',ROOT/'scripts/verify-portable-combat.py')
        cls.core=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.core)
        cls.case=json.loads((ROOT/'tests/fixtures/portable-burst-charge-speed.json').read_text())['cases'][0]

    def test_original_references_are_literal_and_separate_from_weapon_gauge(self):
        before=copy.deepcopy(self.case);words,_=self.core.compile_case(self.case)
        from portable_runtime import double_words
        at=L['BURST_REFERENCE_BASE']
        self.assertEqual(words[at:at+2],[1,31])
        self.assertEqual(words[at+8:at+12],double_words(2)+double_words(.25))
        self.assertEqual(self.case,before)
        self.assertEqual((len(words),L['OUTPUT_WORDS']),(86016,159744))
        c=copy.deepcopy(self.case);c['environment']['burst_references'][0].pop('burst_energy_raw')
        words,_=self.core.compile_case(c);self.assertEqual(words[at+1],30);self.assertEqual(words[at+10:at+12],[0,0])

    def test_invalid_reference_and_history_inputs_fail_closed(self):
        variants=[[],[{}],{},None]
        for value in variants[:-1]:
            c=copy.deepcopy(self.case);c['environment']['burst_references']=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.core.compile_case(c)
        for key,value in [('burst_energy',-1),('burst_energy',True),('burst_energy',float('nan')),('burst_energy_raw',float('inf')),('burst_energy',1000001),('unknown',1)]:
            c=copy.deepcopy(self.case);c['environment']['burst_references'][0][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.core.compile_case(c)
        c=copy.deepcopy(self.case);c.pop('combat')
        with self.assertRaises(ValueError):self.core.compile_case(c)

    def test_new_mutable_history_is_explicitly_initialized(self):
        generated=runtime_initializer()
        self.assertIn('s.normalLandedMask = 0;',generated)
        self.assertEqual((ROOT/'gpu/runtime_init.slang').read_text(),generated)


if __name__=='__main__':unittest.main()
