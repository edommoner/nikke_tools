import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import LIMITS as L, FIELDS as F
from portable_target_state_specs import parse
from portable_trigger_specs import validate_input


class TargetStateContracts(unittest.TestCase):
    def test_opaque_names_and_integer_bounds(self):
        self.assertEqual(parse('target_stack_above:A:B:2'),(6,'A:B',2))
        self.assertEqual(parse('target_stack_above::0'),(6,'',0))
        self.assertEqual(parse('target_stack_above: A :2147483647'),(6,' A ',2147483647))
        for suffix in ('-1','.5','1.0','nan','inf','2147483648','１'):
            with self.subTest(suffix=suffix),self.assertRaises(ValueError):
                validate_input(dict(trigger=dict(timing=['on_attack'],condition=['target_stack_above:A:'+suffix])))

    def test_compiler_preserves_caller_and_exact_name_identity(self):
        spec=importlib.util.spec_from_file_location('target_cases',ROOT/'scripts/verify-portable-combat.py')
        core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
        cases=json.loads((ROOT/'tests/fixtures/portable-target-states.json').read_text())['cases']
        case=next(c for c in cases if c['name']=='target-state-exact-0-2-target_stack_above:')
        before=copy.deepcopy(case);words,metadata=core.compile_case(case)
        at=L['CONDITION_BASE']+L['CONDITION_WORDS']
        self.assertEqual(words[at:at+2],[6,metadata['states']['A:B:C']])
        self.assertEqual(case,before)

    def test_stack_placeholder_preserves_native_runtime_and_merge_policy(self):
        spec=importlib.util.spec_from_file_location('target_flags',ROOT/'scripts/verify-portable-combat.py')
        core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
        cases=json.loads((ROOT/'tests/fixtures/portable-target-states.json').read_text())['cases']
        case=copy.deepcopy(next(c for c in cases if c['name']=='target-state-alias-0-self--1'))
        words,_=core.compile_case(case)
        self.assertEqual(words[L['DEFINITION_BASE']+F['FLAGS']]&2,0)
        self.assertEqual(words[L['RECIPIENT_BASE']+7]&1,1)
        case['effects'][0]['trigger']['condition'].append('during_full_burst')
        words,_=core.compile_case(case)
        self.assertEqual(words[L['DEFINITION_BASE']+F['FLAGS']]&2,2)
        self.assertEqual(words[L['RECIPIENT_BASE']+7]&1,0)


if __name__=='__main__':unittest.main()
