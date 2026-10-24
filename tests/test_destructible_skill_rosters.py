"""Original skill selectors and burst families before shared GPU admission."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from destructible_skill_roster_cases import fixtures
from world_destructible_weapon_roster_native import observe
from portable_destructible_skill_roster_contracts import verify
from destructible_skill_shield_policy import skill

class SkillShieldRosterTests(unittest.TestCase):
 def test_all_seven_original_skills_and_seventy_three_prepared_definitions(self):
  original=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())['레이']
  from calculator import timeline
  with patch.object(timeline,'simulate',side_effect=AssertionError('No battle for static original definitions')):
   for c in fixtures():
    p=engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));self.assertEqual(len(p['effects']),73)
    own=[r['effect'] for r in p['effects'] if r['owner']=='레이' and r['effect'].get('source') in ('스킬1','스킬2','스킬3')];self.assertEqual(own,original)
    self.assertEqual([e['target'] for e in own if e['type']=='damage'],['enemies_nearest_in_range','all_enemies'])
 def test_native_hp_credit_break_and_full_original_skill_factors(self):
  for c in fixtures():
   before=copy.deepcopy(c);n,_=observe(c);result=verify(c,n);self.assertEqual(c,before)
   self.assertFalse(result['gpu_connected']);self.assertFalse(result['in_game_rules_verified']);self.assertFalse(result['full_character_verified'])
 def test_target_spelling_and_burst_family_never_rewritten(self):
  c=fixtures()[1];n,_=observe(c)
  self.assertTrue(n['shield_samples'][20]['family_flags']['is_single_burst'])
  self.assertFalse(n['shield_samples'][30]['family_flags']['is_burst_damage'])
  self.assertEqual(n['packet_samples'][30]['source'],6)
 def test_static_skill_policy_retains_original_values_and_selectors(self):
  c=fixtures()[1];p=engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));chars={c['name']:c for c in p['chars']}
  original=copy.deepcopy(p)
  plans=[skill(r['effect'],chars[r['owner']]) for r in p['effects'] if r['effect']['type']=='damage']
  self.assertEqual([r['route'] for r in plans],[6,2,7]);self.assertEqual(p,original)
 def test_undeclared_skill_shapes_fail_before_interception(self):
  base=dict(source='스킬1',type='damage',name='test',stat='damage',target='all_enemies',fixed_value=100,trigger=dict(timing=['battle_start'],condition=[]));char=dict(name='레이',skill_levels={'1':10,'2':10,'3':10})
  for change in [dict(stat='split_damage'),dict(stat='damage:2'),dict(stat='dot_damage'),dict(target='target'),dict(target='all_projectiles'),dict(target='enemies_random:1'),dict(scaling='max_hp_additive'),dict(damage_formula='normal_attack'),dict(tick_interval=1),dict(fixed_value=-1),dict(trigger=dict(timing=['battle_start'],condition=['target_is_boss']))]:
   with self.subTest(change=change),self.assertRaises(ValueError):skill(dict(base,**change),char)
 def test_explicit_policy_requires_boolean_and_owner(self):
  from destructible_battle_runtime import typed_battle
  from destructible_shield_policy import BOSS
  for kw in (dict(skill_shields=1,shield_owner=BOSS),dict(skill_shields=True),dict(skill_shields=True,shield_owner=BOSS)):
   with self.assertRaises(ValueError):
    with typed_battle(fixtures()[0]['typed_bindings'],**kw):pass
 def test_add_world_is_rejected_and_failure_restores_native_functions(self):
  from calculator import timeline,buff_manager
  c=fixtures()[1];c['body']['enemy']['patterns'].append(dict(id='adds',kind='summon',spec=dict(count=1,hp=1000)))
  old=(timeline.simulate,timeline.calc_damage,timeline.HitEvent,timeline.BuffManager,timeline.CharState._fire,buff_manager.BuffManager.apply_shared_body_heal)
  with self.assertRaisesRegex(ValueError,'single boss'):observe(c)
  self.assertEqual(old,(timeline.simulate,timeline.calc_damage,timeline.HitEvent,timeline.BuffManager,timeline.CharState._fire,buff_manager.BuffManager.apply_shared_body_heal))
 def test_unknown_field_or_injected_scalar_failure_restores_every_scope(self):
  from calculator import timeline,buff_manager
  import destructible_damage_policy
  old=(timeline.simulate,timeline.calc_damage,timeline.HitEvent,timeline.BuffManager,timeline.CharState._fire,buff_manager.BuffManager.apply_shared_body_heal)
  with patch.object(destructible_damage_policy,'calculate',side_effect=RuntimeError('injected skill scalar failure')):
   with self.assertRaisesRegex(RuntimeError,'injected'):observe(fixtures()[1])
  self.assertEqual(old,(timeline.simulate,timeline.calc_damage,timeline.HitEvent,timeline.BuffManager,timeline.CharState._fire,buff_manager.BuffManager.apply_shared_body_heal))

if __name__=='__main__':unittest.main()
