import copy,importlib.util,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_protection_oracle import observe
from portable_specs import LIMITS as L
s=importlib.util.spec_from_file_location('split_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
CASES=json.loads((R/'tests/fixtures/portable-split.json').read_text())['cases']
def native(name):return observe(next(c for c in CASES if c['name']=='split-'+name))
class SplitContracts(unittest.TestCase):
 def test_one_damage_is_divided_without_integer_rounding(self):
  r=native('all-1-1');self.assertEqual([x['damage'] for x in r['hits']],[.2]*5);self.assertEqual([x['hp'] for x in r['queries'][0]['allies']],[999.8]*5)
 def test_every_direct_target_is_a_separate_group(self):
  r=native('all-31-150');self.assertEqual(len(r['hits']),25);self.assertEqual([x['received_hits'] for x in r['queries'][0]['allies']],[5]*5)
 def test_only_original_defense_is_applied(self):
  r=native('original-defense-only');self.assertEqual([x['damage'] for x in r['hits']],[50]*5)
 def test_received_notification_is_direct_only_and_cover_is_per_member(self):
  r=native('direct-only-hit-notify');self.assertEqual(r['queries'][0]['attack_buffs'][0],10);self.assertEqual(len([e for e in r['events'] if e['event']=='received_hit']),5)
  r=native('follower-cover-notify');self.assertEqual(r['queries'][0]['attack_buffs'][1],10)
 def test_group_is_frozen_for_current_primary_then_recomputed(self):
  r=native('groups-recomputed-for-next-primary');self.assertEqual(len(r['hits']),9);self.assertEqual([x['damage'] for x in r['hits']],[30]*5+[150]*4)
 def test_nested_union_preserves_group_order_and_deduplicates(self):
  r=native('nested-target-order');self.assertEqual([x['owner'] for x in r['hits'][:6]],[0,1,2,1,2,0])
  r=native('duplicate-overlapping-lists');self.assertEqual(len(r['hits']),25)
 def test_lethal_callback_saves_member_but_trace_keeps_actual_hp_loss(self):
  r=native('member-lethal-callback');self.assertEqual(r['hits'][1]['hp'],999);self.assertEqual(r['hits'][1]['hp_after'],1);self.assertFalse(r['hits'][1]['down'])
 def test_recipient_audience_keeps_duplicate_notifications_across_word_boundary(self):
  for count in (10,11,21):self.assertEqual(native('duplicate-audience-'+str(count))['queries'][0]['attack_buffs'][0],count*10)
 def test_alias_identity_includes_order_and_multiplicity(self):
  self.assertEqual(len(native('alias-different-order-stays-separate')['carriers']),2)
  self.assertEqual(len(native('alias-identical-order-refreshes')['carriers']),1)
 def test_composite_leaves_keep_combat_and_instant_admission_guards(self):
  c=copy.deepcopy(CASES[0]);c['effects'][0]['target']=['self',['all_allies_burst_not_casted']]
  with self.assertRaises(ValueError):v.compile_case(c)
  c['effects'][0].update(type='instant',stat='heal_hp_pct',fixed_value=10,target=['self','self'])
  with self.assertRaises(ValueError):v.compile_case(c)
 def test_union_is_static_metadata_not_cpu_selected_recipients(self):
  c=copy.deepcopy(next(c for c in CASES if c['name']=='split-nested-target-order'));original=copy.deepcopy(c);words,_=v.compile_case(c);self.assertEqual(c,original)
  self.assertEqual(words[L['RECIPIENT_BASE']],17);self.assertGreater(words[L['RECIPIENT_META_BASE']],0);self.assertEqual(L['SPLIT_HIT_BASE'],135168)
  c['effects'][0]['target']=['self','allies_random:2']
  with self.assertRaises(ValueError):v.compile_case(c)
if __name__=='__main__':unittest.main()
