"""Native contracts that distinguish captured targets from subsequent aiming."""
import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
s=importlib.util.spec_from_file_location('counter_context_contract','research/characterize-world-counter-context.py');contract=importlib.util.module_from_spec(s);s.loader.exec_module(contract)

class CounterContextContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cases={c['name']:c for c in contract.cases.fixtures(contract.physical)}
 def inspect(self,name):return contract.inspect_case(self.cases[name])
 def test_fatal_add_completion_retains_target_but_generic_named_child_clears_it(self):
  captured=self.inspect('add-completion-versus-lifesteal-order-target_is_add')['condition_observations'][0]
  cleared=self.inspect('add-completion-versus-lifesteal-order-generic-named-child-clears-target')['condition_observations'][0]
  self.assertEqual((captured['target']['kind'],captured['accepted']),(5,True));self.assertIsNone(cleared['target']);self.assertFalse(cleared['accepted'])
 def test_death_without_impact_keeps_the_completion_actor(self):
  row=self.inspect('fatal-death-completion-without-impact-target_is_add')['condition_observations'][0]
  self.assertIsNone(row['impact']);self.assertEqual(row['target'],row['completion_actor']);self.assertTrue(row['accepted'])
 def test_enemy_counter_is_not_self_state_but_its_stack_is_visible_to_owner(self):
  absent=self.inspect('body-completion-versus-lifesteal-order-self_state:marker')
  stack=self.inspect('body-completion-versus-lifesteal-order-self_stack_above:marker:1')
  self.assertFalse(absent['condition_observations'][0]['accepted']);self.assertTrue(stack['condition_observations'][0]['accepted'])
  self.assertEqual(stack['native']['allies'][0]['hp'],596.8)
 def test_finite_condition_latches_while_permanent_condition_rechecks_after_retirement(self):
  finite=self.inspect('finite-condition-latches-before-counter-retirement-body-completion-versus-lifesteal-order')
  permanent=self.inspect('runtime-query-after-counter-retirement-body-completion-versus-lifesteal-order')
  self.assertEqual(finite['native']['allies'][0]['hp'],984);self.assertEqual(permanent['native']['allies'][0]['hp'],596.8)
 def test_shared_counter_compiler_keeps_previous_41_literal_inputs_exact(self):
  import hashlib,struct
  rows,programs,bad=contract.physical.prepare();words=[p[0] for p in programs]+[w for _,w in bad]
  golden=json.loads((ROOT/'research/portable-world-counter-landing-short-expected.json').read_text())
  self.assertEqual(len(words),41)
  for w,e in zip(words,golden['entries']):self.assertEqual(hashlib.sha256(struct.pack('<'+'I'*len(w),*w)).hexdigest(),e['input_sha256'])
if __name__=='__main__':unittest.main()
