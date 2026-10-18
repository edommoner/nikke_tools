import sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'app')]
from lifecycle_carrier_cases import callback_identity_cases,recipient_instance_cases
from effect_runtime import active_carrier,state,protection_activation,CATALOG
from unittest.mock import patch

class LifecycleCarrierTests(unittest.TestCase):
 def test_all_existing_callbacks_update_only_current_carrier(self):
  for row in callback_identity_cases():
   with self.subTest(operation=row['operation']):self.assertTrue(row['contract_satisfied'],row)
 def test_actual_activation_keeps_distinct_recipients_and_quantities(self):
  for row in recipient_instance_cases():
   with self.subTest(stat=row['stat']):self.assertTrue(row['passed'],row)
 def test_missing_removed_or_foreign_carrier_never_falls_back_to_sibling(self):
  effect={};other={};old=NS(effect=effect,caster='a');new=NS(effect=effect,caster='a');manager=NS(_active=[old,new])
  self.assertIsNone(active_carrier(manager,effect,'a'))
  state(manager).activation_stack.append(new)
  self.assertIs(active_carrier(manager,effect,'a'),new)
  self.assertIsNone(active_carrier(manager,other,'a'));self.assertIsNone(active_carrier(manager,effect,'b'))
  self.assertIsNone(active_carrier(manager,effect,'a',None))
  manager._active=[old];self.assertIsNone(active_carrier(manager,effect,'a'))
 def test_protection_nested_delivery_and_error_restore_same_context(self):
  effect={};a=NS(effect=effect,caster='a');b=NS(effect=effect,caster='a');manager=NS(_active=[a,b]);seen=[]
  def emit(phase,owner,definition,caster,t,targets):
   seen.append(active_carrier(owner,definition,caster))
   if targets==['outer']:
    protection_activation(owner,definition,caster,t,['inner'],b)
    seen.append(active_carrier(owner,definition,caster));raise ValueError('witness')
  with patch.object(CATALOG,'emit',emit),self.assertRaises(ValueError):protection_activation(manager,effect,'a',0,['outer'],a)
  self.assertEqual(seen,[a,b,a]);self.assertEqual(state(manager).activation_stack,[])

if __name__=='__main__':unittest.main()
