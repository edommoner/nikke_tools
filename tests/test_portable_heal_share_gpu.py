"""Shared admission boundaries and literal source-compatible plan inputs."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_runtime import validate_effect,UnsupportedPortable
from portable_damage_specs import STATS
from effect_spec import EXTRA_STAT
from portable_heal_share_cases import fixtures

class HealShareGPUTests(unittest.TestCase):
    def test_presence_reuses_canonical75_outside_numeric_vector(self):
        self.assertEqual(STATS['heal_split'],EXTRA_STAT['heal_split']);self.assertEqual(STATS['heal_split'],75)
        case=fixtures()[1];effect=case['effects'][1]
        for value in (0,1,-7):
            validate_effect(dict(effect,fixed_value=value),combat=case['combat'],world_frame=True)
    def test_host_rejects_missing_world_wrong_kind_and_unproven_scaling(self):
        case=fixtures()[1];effect=case['effects'][1]
        for eff,combat,world in ((effect,None,True),(effect,case['combat'],False),(dict(effect,type='instant'),case['combat'],True),(dict(effect,scaling='stack_count'),case['combat'],True)):
            with self.subTest(eff=eff,world=world),self.assertRaises(UnsupportedPortable):validate_effect(eff,combat=combat,world_frame=world)
    def test_all43_literal_programs_lower_without_mutating_inputs(self):
        spec=importlib.util.spec_from_file_location('heal_world_cases_test',ROOT/'research/verify-world-heal-share-short.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        cases=m.fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),43)
        for case in cases:
            with self.subTest(case=case['name']):m.suite.compile_case(case)
        self.assertEqual(cases,before)
