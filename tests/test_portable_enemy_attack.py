"""Base-attack data and selector admission, independent of GPU rank output."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import validate_effect
from portable_specs import LIMITS as L
from calculator.boss_pattern import DEFAULT_BOSS_ATK
spec=importlib.util.spec_from_file_location('attack_rank_verifier',ROOT/'scripts/verify-portable-combat.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class EnemyAttackInputTests(unittest.TestCase):
    def case(self):return next(c for c in v.fixtures() if c['name']=='enemy-attack-default-body')
    def test_native_defaults_and_no_serialized_rank(self):
        words,_=v.compile_case(self.case());at=L['TARGET_ATTACK_BASE']
        values=struct.unpack('<8d',struct.pack('<16I',*words[at:at+16]))
        self.assertEqual(values,(DEFAULT_BOSS_ATK,0,0,0,0,0,0,0))
        self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS']),(77824,94208))
    def test_invalid_attack_data_is_rejected_before_dispatch(self):
        for value in (float('nan'),float('inf'),-1,1e31,True,9007199254740993,10**1000):
            case=copy.deepcopy(self.case());case['combat']['targets'][1]['attack']=value
            with self.subTest(value=value),self.assertRaises(ValueError):v.compile_case(case)
    def test_count_range_and_periodic_clock_are_preserved(self):
        effect=self.case()['effects'][1]
        for count in (1,256):validate_effect({**effect,'target':f'enemies_top_atk:{count}'},combat={})
        for count in ('0','257','-1','1.5',''):
            with self.subTest(count=count),self.assertRaises(ValueError):validate_effect({**effect,'target':'enemies_top_atk:'+count},combat={})
        periodic={**effect,'target':'enemies_top_atk:1','tick_interval':.1,'duration':1};validate_effect(periodic,combat={})
        from portable_periodic_specs import periodic_flags
        self.assertEqual(periodic_flags(periodic,0)&1,1)
    def test_real_preparation_keeps_authored_enemy_attack(self):
        from detail_coverage import body_for
        import engine_worker
        from portable_roster_input import compile_static_battle
        prepared=engine_worker.evaluate({**body_for(['미란다','도라','드레이크','N102','메어리']),'burst_gauge_mode':'accumulate','_portable_static_inputs':True})
        prepared['enemy']['atk']=54321
        words,_=compile_static_battle(prepared)
        self.assertEqual(struct.unpack('<d',struct.pack('<2I',*words[L['TARGET_ATTACK_BASE']:L['TARGET_ATTACK_BASE']+2]))[0],54321)

if __name__=='__main__':unittest.main()
