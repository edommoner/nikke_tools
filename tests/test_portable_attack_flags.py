import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import LIMITS as L,FIELDS as F


class AttackFlagContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('attack_flags_core',ROOT/'scripts/verify-portable-combat.py')
        cls.core=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.core)
        cls.cases=json.loads((ROOT/'tests/fixtures/portable-attack-flags.json').read_text())['cases']

    def test_boolean_definitions_use_existing_slots_without_mutation(self):
        for stat,slot in [('pierce_enabled',36),('armor_break_enabled',52)]:
            c=copy.deepcopy(next(c for c in self.cases if c['name']==f'attack-flag-presence-0-{stat}-1-self'))
            before=copy.deepcopy(c);words,_=self.core.compile_case(c)
            self.assertEqual(c,before);self.assertEqual(len(words),86016)
            self.assertEqual(words[L['DEFINITION_BASE']+3*L['DEFINITION_WORDS']+F['STAT']],slot)
            self.assertEqual(L['OUTPUT_WORDS'],159744)

    def test_flags_reject_enemy_recipients_and_nonfinite_literals(self):
        for stat in ('pierce_enabled','armor_break_enabled'):
            original=next(c for c in self.cases if c['name']==f'attack-flag-presence-0-{stat}-1-self')
            for key,value in [('target','boss'),('fixed_value',float('nan')),('fixed_value',float('inf')),('values',{'10':float('nan')}),('values',[100])]:
                c=copy.deepcopy(original);c['effects'][-1][key]=value
                with self.subTest(stat=stat,key=key,value=value),self.assertRaises(ValueError):self.core.compile_case(c)


if __name__=='__main__':unittest.main()
