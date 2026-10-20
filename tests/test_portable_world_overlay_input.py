"""Private overlay compilation must remain literal and keep normal admission shut."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('private_overlay_input',ROOT/'research/verify-world-overlay-body.py');body=importlib.util.module_from_spec(spec);spec.loader.exec_module(body)
from calculator.boss_pattern import BossScript
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L
from portable_world_overlay_specs import compiler_effect

class OverlayInput(unittest.TestCase):
 def test_skill_mode_is_literal_and_does_not_open_normal_admission(self):
  case=next(c for c in body.module('overlay_skill_input','research/world_overlay_skill_mode_cases.py').fixtures() if c['name']=='weapon-mode-vanish-True');before=copy.deepcopy(case)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU tick may become GPU input')):words,_=body.compile_case(case)
  self.assertEqual(case,before);self.assertEqual(words[L['MODE_BASE']+31],1)
  with self.assertRaises(UnsupportedPortable):validate_effect(case['effects'][0],combat=case['combat'],world_frame=True)
 def test_false_skill_policy_stays_literal_and_wrong_types_fail(self):
  original=dict(type='weapon_change',name='mode',skill_damage=False);self.assertNotIn('skill_damage',compiler_effect(original));self.assertIs(original['skill_damage'],False)
  for value in (0,1,None,'false',[]):
   with self.subTest(value=value),self.assertRaises(ValueError):compiler_effect(dict(original,skill_damage=value))
 def test_huge_cleanse_count_is_not_preconverted_or_applied_on_cpu(self):
  case=next(c for c in body.module('overlay_cleanse_input','research/world_overlay_cleanse_cases.py').fixtures() if c['name']=='cleanse-count-1e+308');before=copy.deepcopy(case)
  with patch.object(BossScript,'dispel',side_effect=AssertionError('CPU state is not input')),patch.object(BossScript,'begin_frame',side_effect=AssertionError('CPU state is not input')):words,_=body.compile_case(case)
  self.assertEqual(case,before);at=L['DEFINITION_BASE']+6;self.assertEqual(struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0],1e308)
  with self.assertRaises(UnsupportedPortable):validate_effect(case['effects'][0],combat=case['combat'],world_frame=True)
 def test_cleanse_stat_requires_instant_type(self):
  with self.assertRaises(ValueError):compiler_effect(dict(type='buff',stat='enemy_buff_cleanse',fixed_value=1))
if __name__=='__main__':unittest.main()
