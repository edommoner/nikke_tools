"""Actor source descriptors remain literal;live generations are GPU-owned."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('actor_input_driver',ROOT/'research/verify-world-actors.py');driver=importlib.util.module_from_spec(s);s.loader.exec_module(driver)
from portable_actor_specs import compile_registry
from portable_specs import ABI,LIMITS as L
from calculator.boss_pattern import BossScript,validate

class ActorInput(unittest.TestCase):
 def test128_bindings_compile_without_cpu_world_tick(self):
  case=next(c for c in driver.cases() if c['name']=='128-actors-127-adds');before=copy.deepcopy(case)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('CPU lifecycle must not be input')):words,rows=driver.compile_case(case)
  self.assertEqual(case,before);self.assertEqual(len(rows),128);self.assertEqual(words[L['WORLD_ACTOR_INPUT_BASE']+1],128);self.assertEqual(len(words),L['WORLD_ACTOR_INPUT_WORDS'])
 def test_capacity_is_checked_before_expanding_the_binding_table(self):
  patterns=validate([dict(id='many',kind='summon',spec=dict(count=1000000000,hp=1))])
  with patch('portable_actor_specs.bindings',side_effect=AssertionError('Must reject before allocation')),self.assertRaisesRegex(ValueError,'capacity'):compile_registry(patterns)
 def test_registry_does_not_silently_drop_unconnected_combat_lifecycles(self):
  patterns=[dict(id='parts',kind='parts',targets=[dict(name='part',hp=10)],until=dict(targets_cleared=True)),dict(id='wave',kind='summon',spec=dict(count=1,hp=10,attack=dict(atk=10,coeff=100,target='all'))),dict(id='interrupt',kind='interrupt',targets=[dict(name='target',hp=10)])]
  for p in patterns:
   with self.subTest(kind=p['kind']),self.assertRaises(ValueError):compile_registry(validate([p]))
 def test_normal_layout_stays_separate_from128_actor_capacity(self):
  self.assertEqual((ABI,L['INPUT_WORDS'],L['OUTPUT_WORDS']),(0x50455673,86016,159744));self.assertEqual(L['WORLD_ACTORS'],128);self.assertLessEqual(L['WORLD_ACTOR_QUERY_BASE']+L['COMMANDS']*8,L['WORLD_FRAME_OUTPUT_WORDS'])
if __name__=='__main__':unittest.main()
