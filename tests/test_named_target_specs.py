"""One shared reference contract, not a copy of each character's skills."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from named_target_specs import resolve_named_attack

class NamedTargetSpecsTests(unittest.TestCase):
 def setUp(self):
  self.attack={'name':'attack','type':'damage','stat':'sequential_damage:10','target':'enemies_random'}
  self.bonus={'type':'damage','stat':'bonus_damage','target':'same_target:attack','scaling':'stack_count','scaling_ref':'different stack'}
 def test_repetition_is_separate_from_coefficient_scaling_and_owner(self):
  result=resolve_named_attack(self.bonus,'a',[(self.attack,'a'),(self.attack,'b')])
  self.assertEqual(result.deferred_bonus_hits,10);self.assertEqual(result.reference,'attack')
  one={**self.attack,'stat':'burst_damage'}
  self.assertEqual(resolve_named_attack(self.bonus,'a',[(one,'a')]).deferred_bonus_hits,1)
  self.assertIsNone(resolve_named_attack({'target':'target'},'a',[]))
 def test_invalid_or_ambiguous_references_are_rejected(self):
  cases=[([],self.bonus),([(self.attack,'b')],self.bonus),([(self.attack,'a')]*2,self.bonus)]
  for changes in ({'stat':'sequential_damage:state'},{'stat':'sequential_damage:0'},{'stat':'sequential_damage:4097'},{'stat':'damage:2:3'},{'type':'buff'},{'target':'all_allies'},{'target':'same_target:cycle'}):
   cases.append(([({**self.attack,**changes},'a')],self.bonus))
  cases.extend([([(self.attack,'a')],{**self.bonus,**changes}) for changes in ({'target':'same_target:'},{'stat':'dot_damage','tick_interval':1},{'type':'buff'})])
  for effects,bonus in cases:
   with self.subTest(effects=effects,bonus=bonus),self.assertRaises(ValueError):resolve_named_attack(bonus,'a',effects)

if __name__=='__main__':unittest.main()
