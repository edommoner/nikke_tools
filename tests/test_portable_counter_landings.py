import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
s=importlib.util.spec_from_file_location('counter_landing_packer',ROOT/'research/compile-world-target-counter-battles.py');driver=importlib.util.module_from_spec(s);s.loader.exec_module(driver)
from world_frame_native import observe
from portable_target_counter_specs import ACTION_BASE
from portable_specs import LIMITS as L,FIELDS as F

class PhysicalCounterContracts(unittest.TestCase):
 def test_counter_callback_changes_same_hit_lifesteal_before_heal_and_damage_is_clipped_only_for_add(self):
  rows=driver.fixtures()
  for index,damage in [(0,968),(1,50),(3,1)]:
   result=observe(rows[index]);counter=result['target_counters'];self.assertEqual(result['allies'][0]['hp'],984)
   self.assertEqual(counter['completions'][0]['impact']['damage'],damage)
   events=counter['events'];callback=next(i for i,e in enumerate(events) if e['event'].startswith('event:target_counter_complete:'))
   heal=next(i for i,e in enumerate(events) if e['event']=='event:heal_received');self.assertLess(callback,heal)
 def test_mode_damage_formula_cannot_select_the_counter_credit_family(self):
  cases={c['name']:c for c in driver.fixtures()}
  ignored=observe(cases['skill-mode-1-pellets-credit-family-skill'])['target_counters'];self.assertEqual(ignored['completions'],[]);self.assertEqual(ignored['resources'][0]['credit'],0)
  actual=observe(cases['skill-mode-single-physical-weapon-family-positive'])['target_counters'];self.assertEqual(actual['completions'][0]['impact']['family'],0)
 def test_world_input_uses_authored_bindings_and_reach_without_cpu_observations(self):
  case=next(c for c in driver.fixtures() if c['name']=='part-50-completion-versus-lifesteal-order');words,meta,bindings=driver.compile_case(case)
  self.assertEqual(words[0],driver.PENDING_ABI);self.assertEqual(words[L['TARGET_COUNTER_INPUT_BASE']+6],1)
  slot=next(i for i,b in enumerate(bindings) if int(b.kind)==1);at=L['TARGET_COUNTER_INPUT_BASE']+ACTION_BASE+slot*8;self.assertEqual(words[at:at+8],[1,1,0,0,0,0,0,0])
  poisoned=copy.deepcopy(case);poisoned['native']={'credit':999,'dead':True};self.assertEqual(words,driver.compile_case(poisoned)[0])
 def test_non_sentinel_world_binding_rejects_before_gpu_and_counter_never_merges_with_defense_buff(self):
  case=copy.deepcopy(driver.fixtures()[1]);case['effects'][2]['target']='target'
  with self.assertRaisesRegex(ValueError,'boss sentinel'):driver.compile_case(case)
  case=copy.deepcopy(driver.fixtures()[0]);case['effects'].append(dict(name='defense',type='buff',stat='def_pct',fixed_value=10,target='boss',duration=10,trigger=dict(timing=['battle_start'],condition=[])));case['owners'].append(0)
  words,_,_=driver.compile_case(case);base=L['RECIPIENT_BASE'];self.assertNotEqual(words[base+2*8+6],words[base+4*8+6])
  self.assertEqual([words[L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F[k]] for k in ('KIND','STAT')],[4,0])
if __name__=='__main__':unittest.main()
