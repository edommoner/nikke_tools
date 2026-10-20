import copy,importlib.util,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_instant_list_oracle import observe
from portable_specs import LIMITS as L
s=importlib.util.spec_from_file_location('instant_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
CASES=json.loads((R/'tests/fixtures/portable-instant-lists.json').read_text())['cases']
def native(name):return observe(next(c for c in CASES if c['name']=='instant-list-'+name))
class OrderedInstantContracts(unittest.TestCase):
 def test_all_twenty_one_heals_are_delivered(self):self.assertEqual(native('heal-21')['queries'][0]['allies'][0]['hp'],310)
 def test_rank_selection_is_frozen_before_any_heal(self):self.assertEqual([r['hp'] for r in native('rank-frozen-before-first-delivery')['queries'][0]['allies']],[1000,200,300,400,500])
 def test_zero_and_overheal_each_notify_twenty_one_times(self):
  for name in ('heal-zero-still-notifies','heal-full-still-notifies'):self.assertEqual(native(name)['queries'][0]['attack_buffs'][0],210)
 def test_caster_basis_is_live_between_deliveries(self):self.assertEqual(native('heal-live-caster-basis-between-children')['queries'][0]['allies'][0]['max_hp'],3100)
 def test_current_hp_reduction_repeats_instead_of_deduplicating(self):
  hp=native('reduce-21')['queries'][0]['allies'][0]['hp'];self.assertGreater(hp,10);self.assertLess(hp,11)
 def test_cover_revival_and_zero_healing_do_not_emit_recovery(self):
  r=native('cover_revive-0');self.assertEqual(r['queries'][0]['covers'][0]['hp'],100);self.assertEqual(r['queries'][0]['attack_buffs'][0],0)
  self.assertEqual(native('cover-zero-1000')['queries'][0]['attack_buffs'][0],0)
 def test_shield_and_decoy_capacity_is_reused_for_each_delivery(self):
  for stat,key in (('shield_from_max_hp_pct','shield'),('decoy','decoy')):self.assertEqual(native(stat+'-heal-None')['protection'][0][key],142)
 def test_ammo_integer_rules_and_one_completion_event(self):
  self.assertEqual(native('ammo_charge_flat--1')['queries'][0]['combat']['weapons'][0]['ammo'],79)
  self.assertEqual(native('ammo_charge_flat--0.9')['queries'][0]['combat']['weapons'][0]['ammo'],100)
  self.assertEqual(native('ammo_charge_pct--10')['queries'][0]['attack_buffs'][0],10)
  self.assertEqual(native('ammo_charge_pct-empty-members')['queries'][0]['attack_buffs'][0],10)
 def test_shared_gauge_is_once_but_cooldown_is_per_recipient(self):
  self.assertEqual(native('shared-gauge-once-21')['queries'][0]['combat']['gauge'],10)
  self.assertEqual(native('cooldown-21')['queries'][0]['combat']['weapons'][0]['ready'],.1)
 def test_periodic_heal_delays_first_tick_and_excludes_expiry(self):self.assertEqual([q['allies'][0]['hp'] for q in native('periodic-heal-keeps-all-deliveries')['queries']],[100,310,310])
 def test_original_definitions_remain_unmodified_and_long_lists_fail(self):
  c=copy.deepcopy(CASES[4]);before=copy.deepcopy(c);words,_=v.compile_case(c);self.assertEqual(c,before);self.assertEqual(words[L['RECIPIENT_BASE']],17)
  c['effects'][0]['target']=['self']*22
  with self.assertRaises(ValueError):v.compile_case(c)
if __name__=='__main__':unittest.main()
