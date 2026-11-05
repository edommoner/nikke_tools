"""Enemy field recipients must distinguish completion targets from live aim."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
s=importlib.util.spec_from_file_location('field_contract','research/characterize-world-counter-fields.py');contract=importlib.util.module_from_spec(s);s.loader.exec_module(contract)
class CounterFieldContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cases={c['name']:c for c in contract.cases.fixtures(contract.physical)}
 def inspect(self,name):return contract.inspect_case(self.cases[name])
 def test_fatal_completion_field_keeps_dead_actor_without_aliasing_next_add(self):
  r=self.inspect('fatal-first-add-current-field-keeps-dead-actor')
  self.assertEqual(r['field_activations'][0]['target'],dict(kind=5,identity=0,generation=1))
  self.assertEqual(r['native']['enemy_fields']['carriers'][0]['actor'],[5,0,1])
 def test_nested_generic_field_child_uses_new_current_add(self):
  r=self.inspect('nested-generic-field-child-uses-new-current-add');a=r['field_activations']
  self.assertIsNone(a[1]['target']);self.assertNotEqual(a[0]['targets'],a[1]['targets'])
  self.assertEqual([x['actor'] for x in r['native']['enemy_fields']['carriers']],[[5,0,1],[5,1,1]])
 def test_all128_receivers_complete_before_counter_marker_retires(self):
  r=self.inspect('counter-field-fanout128-holds-completion-marker')
  self.assertEqual(len(r['field_activations']),128)
  self.assertEqual(next(x['stack'] for x in r['native']['named_state']['allied_carriers'] if x['name']=='fanout-witness'),128)
 def test_refresh_inside_completion_preserves_new_counter_epoch(self):
  r=self.inspect('counter-refresh-child-retains-new-epoch-and-field')['native']
  self.assertEqual(len(r['target_counters']['completions']),2)
  self.assertEqual(r['enemy_fields']['carriers'][0]['stack'],2)
 def test_part_credit_uses_captured_part_damage_before_field_mutation(self):
  r=self.inspect('part-counter-field-logical-root-with-captured-part-damage')['native']
  self.assertEqual(r['target_counters']['completions'][0]['impact']['damage'],968)
  self.assertEqual(r['enemy_fields']['carriers'][0]['actor'],[0,0,1])
if __name__=='__main__':unittest.main()
