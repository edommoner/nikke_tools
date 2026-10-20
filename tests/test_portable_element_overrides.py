"""Native element presence/lifetime contracts and distinct integer wire IDs."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_element_specs import STAT,legacy_effect
from portable_specs import LIMITS as L,FIELDS as F,ABI
from effect_spec import DETAIL_STAT,EXTRA_STAT
from portable_element_oracle import observe
s=importlib.util.spec_from_file_location('element_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
CASES=json.loads((R/'tests/fixtures/portable-element-overrides.json').read_text())['cases']
def case(suffix):return copy.deepcopy(next(c for c in CASES if c['name']=='element-'+suffix))
class ElementOverrideContracts(unittest.TestCase):
 def test_presence_stat_does_not_alias_legacy_or_numeric_vector(self):
  self.assertNotIn(STAT,set(DETAIL_STAT.values())|set(EXTRA_STAT.values()));self.assertGreaterEqual(STAT,64)
 def test_code_ids_are_integer_payloads_and_amount_is_canonical_zero(self):
  c=case('matrix-2-2-False');c['effects'][1]['fixed_value']=-100;p,m=v.compile_case(c);b=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];w=L['WORLD_META_BASE'];a=L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']
  self.assertEqual(p[b+F['KIND']],0);self.assertEqual(p[b+F['STAT']],STAT);self.assertEqual(p[b+F['VALUE']:b+F['VALUE']+2],[0,0]);self.assertEqual(p[a],p[w]);self.assertEqual(p[w+2],1)
 def test_last_reference_id_is_exact_and_missing_remains_zero(self):
  for missing in (False,True):
   p,m=v.compile_case(case('capacity-256-'+str(missing)));w=L['WORLD_META_BASE'];a=L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']
   self.assertEqual(p[w:w+2],[256,256]);self.assertEqual(p[a],0 if missing else 256)
 def test_missing_code_cannot_be_confused_with_a_name_id(self):
  p,m=v.compile_case(case('matrix-2-0-False'));a=L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS'];self.assertEqual(p[a],0);self.assertGreater(p[L['WORLD_META_BASE']],0)
 def test_empty_world_never_grants_override(self):
  for prefix in ('matrix-0-2-False','matrix-1-1-False'):
   c=case(prefix);self.assertEqual(observe(c)['queries'],observe(case('matrix-0-0-False'))['queries'])
 def test_name_id_zero_has_a_distinct_nonzero_tag(self):
  p,m=v.compile_case(case('name-id-zero'));self.assertEqual(m['states']['전격'],0);self.assertEqual(p[L['WORLD_META_BASE']],1)
 def test_legacy_projection_preserves_authored_effect(self):
  e=case('matrix-2-2-False')['effects'][1];before=copy.deepcopy(e);converted=legacy_effect(e);self.assertEqual(e,before);self.assertNotIn('target_code',converted);self.assertEqual(converted['stat'],'');self.assertEqual(converted['name'],e['name'])
 def test_all_authored_cases_compile_without_input_mutation(self):
  for c in CASES:
   original=copy.deepcopy(c);p,m=v.compile_case(c);self.assertEqual(c,original);self.assertEqual(p[0],ABI);self.assertLessEqual(p[2],L['COMMANDS'])
 def test_original_code_bonus_is_ored_not_added(self):
  c=case('matrix-2-2-True');self.assertEqual(observe(c)['queries'][0]['damage'],[1100]*5)
 def test_ignored_numeric_amount_and_stack_do_not_change_advantage(self):
  for i in range(4):
   for count in (1,5):self.assertEqual(observe(case(f'presence-{i}-{count}'))['queries'][2]['damage'],[3300,3000,3000,3000,3000])
 def test_permanent_passive_presence_does_not_apply_numeric_runtime_filter(self):
  c=case('condition--1-passive-False-0');self.assertEqual(observe(c)['queries'][-1]['damage'],[4400,4000,4000,4000,4000])
 def test_periodic_callback_sees_carrier_before_expiry_cleanup(self):
  c=case('packet-dot_damage-전격');self.assertEqual([q['damage'][0] for q in observe(c)['queries']],[1100,2200,3200,4200])
 def test_ranked_marker_is_not_forced_by_numeric_query(self):
  for target in ('allies_top_atk:1','allies_lowest_hp:1'):self.assertEqual(observe(case('unresolved-'+target))['queries'][-1]['damage'],[4000]*5)
 def test_target_code_field_is_only_admitted_for_its_own_marker(self):
  c=case('matrix-2-2-False');c['effects'][1]['stat']='atk_pct'
  with self.assertRaises(ValueError):v.compile_case(c)
 def test_alias_refresh_retains_original_effect_code(self):
  for same in (False,True):
   c=case(f'alias-True-{same}-작열');self.assertEqual(observe(c)['queries'][-1]['damage'],[4000]*5)
   c=case(f'alias-True-{same}-전격');self.assertEqual(observe(c)['queries'][2]['damage'],[3300,3000,3000,3000,3000])
 def test_physical_shots_consume_presence_per_recipient_after_damage(self):
  self.assertEqual([q['damage'][0] for q in observe(case('physical-bullets-전격-0-self'))['queries']],[1100,2200,3300,4300])
  self.assertEqual([q['damage'][0] for q in observe(case('physical-bullets-전격-4-allies_top_atk:1'))['queries']],[1000,2000,3100,4100])
 def test_invalid_code_types_fail_closed(self):
  for code in (0,False,[],{}):
   c=case('matrix-2-2-False');c['effects'][1]['target_code']=code
   with self.assertRaises(ValueError):v.compile_case(c)
if __name__=='__main__':unittest.main()
