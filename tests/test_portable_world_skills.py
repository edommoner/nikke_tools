"""Full native packet contracts for the common late-routing skill path."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_specs import LIMITS as L
import world_skill_cases as cases
s=importlib.util.spec_from_file_location('skill_test_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
class WorldSkillContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cases={c['name']:c for c in cases.fixtures(physical)}
 def observe(self,name):return physical.observe(self.cases[name])
 def test_counter_free_world_uses_authored_input_without_a_synthetic_counter(self):
  c=self.cases['counter-free-world-skill-all_enemies'];w,_,_=cases.compile_case(physical,c)
  self.assertEqual(w[0],L['WORLD_SKILL_ABI']);self.assertEqual(w[L['TARGET_COUNTER_INPUT_BASE']+6],7)
  self.assertFalse(any(w[L['TARGET_COUNTER_INPUT_BASE']+8:L['TARGET_COUNTER_INPUT_BASE']+4104]))
  with self.assertRaisesRegex(ValueError,'requires a counter'):physical.compile_case(c)
 def test_authored_skill_inputs_ignore_cpu_observations(self):
  c=copy.deepcopy(self.cases['all128-late-skill-recipients']);before=cases.compile_case(physical,c)[0]
  c['native']={'amount':1e20,'targets':[0]*128,'time':99};self.assertEqual(before,cases.compile_case(physical,c)[0])
 def test_multihit_amount_is_captured_before_named_attack_buff(self):
  r=self.observe('multihit3-captures-amount-before-named-buff')
  packets=[e['packet']['damage'] for e in r['target_counters']['events'] if e['event']=='impact_before' and e['packet']['family']==1]
  self.assertEqual(len(packets),3);self.assertEqual(len(set(packets)),1)
 def test_late_all_routing_includes_an_add_born_after_creation(self):
  r=self.observe('late-routing-includes-add-born-after-skill-creation')
  packets=[e for e in r['target_counters']['events'] if e['event']=='impact_before' and e['packet']['family']==1]
  self.assertEqual([p['packet']['target']['kind'] for p in packets],[0,5]);self.assertTrue(all(p['time']>0 for p in packets))
 def test_normal_formula_admission_is_world_only_and_explicit(self):
  from portable_runtime import validate_effect,UnsupportedPortable
  e=copy.deepcopy(next(e for e in self.cases['core-damage-normal-formula-is-skill']['effects'] if e.get('type')=='damage'))
  with self.assertRaises(UnsupportedPortable):validate_effect(e)
  for value in ('',None,'skill',False):
   with self.assertRaises(UnsupportedPortable):validate_effect(dict(e,damage_formula=value),world_frame=True)
 def test_core_tag_is_weapon_but_normal_formula_overrides_to_skill(self):
  from world_skill_native import inspect
  for name,family in [('direct-family-core_damage',0),('core-damage-normal-formula-is-skill',1)]:
   c=self.cases[name];native,trace=inspect(c);self.assertEqual(len(trace),1)
   w,_,_=cases.compile_case(physical,c);row=next(i for i,e in enumerate(c['effects']) if e.get('type')=='damage');self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+row*8+3],family)
   r=self.observe(name);packets=[e['packet'] for e in r['target_counters']['events'] if e['event']=='impact_before' and e['packet']['damage']==trace[0]['amount']]
   self.assertTrue(packets);self.assertTrue(all(p['family']==family for p in packets))
   proof=[v for v in native['target_counters']['completions'] if v['name']=='skill-proof'];self.assertEqual(bool(proof),bool(family))
 def test_split_zero_damage_keeps_independent_positive_skill_credit(self):
  r=self.observe('split128-zero-damage-still-earns-skill-credit')
  packets=[e['packet'] for e in r['target_counters']['events'] if e['event']=='impact_before' and e['packet']['family']==1]
  self.assertEqual(len(packets),128);self.assertTrue(all(p['damage']==0 and p['credit']==1 for p in packets))
  proof=next(c for c in r['target_counters']['completions'] if c['name']=='skill-proof');self.assertEqual(proof['impact']['damage'],0)
if __name__=='__main__':unittest.main()
