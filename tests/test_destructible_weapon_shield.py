"""Guard native weapon context, shot snapshot, pellet order and scope cleanup."""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline,buff_manager
from destructible_battle_runtime import typed_battle
from destructible_shield_policy import BOSS
from destructible_weapon_shield_cases import fixtures
from portable_destructible_weapon_shield_contracts import verify
from world_destructible_shield_battle_native import observe

class WeaponShieldTests(unittest.TestCase):
 def test_twenty_two_literal_real_weapon_battles(self):
  self.assertEqual(len(fixtures()),22)
  for c in fixtures():
   with self.subTest(name=c['name']):self.assertTrue(verify(c,observe(c)[0])['reference_model_gap'])

 def test_disabled_policy_keeps_the_canonical_body_weapon(self):
  c=copy.deepcopy(fixtures()[0]);c['weapon_shield_interception_v1']=False
  n,_=observe(c);self.assertEqual(n['battle']['damage'],[3872,0,0,0,0]);self.assertEqual(n['attacks'],[]);self.assertEqual(n['remaining'],[10000.])

 def test_explicit_boolean_owner_and_modifier_model_required(self):
  for kw in (dict(weapon_shields=1,shield_owner=BOSS),dict(weapon_shields=True),dict(weapon_shields='yes',shield_owner=BOSS)):
   with self.subTest(kw=kw),self.assertRaises(ValueError):
    with typed_battle(fixtures()[0]['typed_bindings'],modifier_model=True,**kw):pass
  with self.assertRaisesRegex(ValueError,'declared modifier model'):
   with typed_battle(fixtures()[0]['typed_bindings'],weapon_shields=True,shield_owner=BOSS):pass

 def test_scalar_and_packet_failure_restore_native_functions(self):
  def identity():return (timeline.CharState._fire,timeline.CharState._charge_fire,timeline.calc_damage,timeline.HitEvent,timeline.simulate,timeline.BuffManager,buff_manager.BuffManager.register_damage_handler,dict(buff_manager._STAT_TO_BUFF))
  before=identity()
  for target in ('destructible_damage_policy.calculate','destructible_weapon_runtime.WeaponShots.take'):
   with patch(target,side_effect=RuntimeError('weapon capture failure')):
    with self.subTest(target=target),self.assertRaisesRegex(RuntimeError,'weapon capture failure'):observe(fixtures()[0])
   self.assertEqual(before,identity())
  verify(fixtures()[0],observe(fixtures()[0])[0])

 def test_part_and_piercing_policy_cannot_silently_alias_body_shields(self):
  c=copy.deepcopy(fixtures()[0]);c['patterns'].insert(0,dict(id='part',kind='parts',targets=[dict(name='test-part',hp=10000,reach=1)],until=dict(time=1.)))
  with self.assertRaisesRegex(ValueError,'geometry/part/interrupt'):observe(c)
  from world_enemy_attack_cases import field
  c=copy.deepcopy(fixtures()[0]);c['effects'].insert(0,field('pierce_enabled',1,'self','unsupported-pierce'));c['owners'].insert(0,0)
  with self.assertRaisesRegex(ValueError,'nonpiercing'):observe(c)
  for stat in ('lifesteal_pct','dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct'):
   c=copy.deepcopy(fixtures()[0]);c['effects'].insert(0,field(stat,1,'self','unsupported-post-landing'));c['owners'].insert(0,0)
   with self.subTest(stat=stat),self.assertRaisesRegex(ValueError,'post-landing'):observe(c)

 def test_secondary_scalar_projection_is_rejected_before_second_sample(self):
  def extra(enemy,ht,res,buffs,**kw):
   return timeline.calc_damage(kw['base_atk'],buffs,kw['weapon'],ht,enemy_def=enemy.get('def',0),expected=kw['expected'])
  with patch.object(timeline,'_reach_hit',extra):
   with self.assertRaisesRegex(ValueError,'scalar projection'):observe(fixtures()[0])

 def test_reference_registry_and_gpu_sources_preserved(self):
  from portable_reference import REFERENCES
  from portable_backend import source_hashes
  self.assertEqual(REFERENCES['destructible-weapon-shield'][0],'destructible_weapon_shield_cases')
  self.assertEqual(source_hashes('gpu/destructible_shield_battle_entry.slang'),json.loads((ROOT/'research/portable-destructible-hit-shield-short-expected.json').read_text())['source_sha256'])

if __name__=='__main__':unittest.main()
