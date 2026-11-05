"""Complete original effects, no CPU event packing, literal live contracts."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('weapon_roster_tests',ROOT/'research/verify-destructible-weapon-rosters-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from portable_destructible_roster_input import compile_weapon_shield_roster
from portable_specs import LIMITS as L,FIELDS as F

from historical_engine_reference import historical_reference

class WeaponRosterTests(unittest.TestCase):
 def prepared(self):
  c=a.fixtures()[0];return c,a.roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True))
 def test_lowering_changes_only_modifier_carrier_kind_stat_and_axis(self):
  from destructible_damage_policy import modifier_axis
  c,p=self.prepared();before=copy.deepcopy(p)
  from portable_runtime import UnsupportedPortable
  with self.assertRaises(UnsupportedPortable):a.roster.compile_projectile_battle(p)
  w,m=compile_weapon_shield_roster(p,c['typed_bindings']);self.assertEqual(p,before)
  with self.assertRaises(UnsupportedPortable):a.roster.compile_projectile_battle(p)
  lowered=copy.deepcopy(p)
  for x in lowered['effects']:
   if modifier_axis(x['effect']):x['effect']['stat']='atk_dmg_pct'
  base,_=a.roster.compile_projectile_battle(lowered)
  expected=list(base)
  for row,index in enumerate(m['binding_source_indices']):
   axis=modifier_axis(p['effects'][index]['effect']);self.assertEqual(w[109568+row],axis)
   if axis:
    at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];expected[at+F['KIND']]=4;expected[at+F['STAT']]=0
  self.assertEqual(w[:104400],expected)
 def test_policy_rejects_geometry_postlanding_and_ambiguous_skill_routes(self):
  c,p=self.prepared()
  for field,value in [('coord',{}),('has_parts',True),('part_break_interval',1)]:
   bad=copy.deepcopy(p);bad['enemy'][field]=value
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'geometry'):compile_weapon_shield_roster(bad,c['typed_bindings'])
  for stat in ('lifesteal_pct','dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct','pierce_enabled'):
   bad=copy.deepcopy(p);bad['effects'][0]['effect']['stat']=stat
   with self.subTest(stat=stat),self.assertRaises(ValueError):compile_weapon_shield_roster(bad,c['typed_bindings'])
  bad=copy.deepcopy(p);bad['effects'][0]['effect'].update(type='damage',target='boss')
  with self.assertRaisesRegex(ValueError,'weapons only'):compile_weapon_shield_roster(bad,c['typed_bindings'])
  for kw in (dict(hit_shields=1),dict(max_attacks=0),dict(max_attacks=129),dict(max_attacks=True)):
   with self.assertRaises(ValueError):compile_weapon_shield_roster(p,c['typed_bindings'],**kw)
  for kind in (0,2,5):
   with self.assertRaisesRegex(ValueError,'shield bindings'):compile_weapon_shield_roster(p,[dict(c['typed_bindings'][0],kind=kind)])
 def test_native_actual_conditional_modifier_and_recovery(self):
  from portable_destructible_weapon_roster_contracts import verify
  for c in a.fixtures():
   n,_=a.observe(c);v=verify(c,n);self.assertEqual(v['positive_modifier_samples'],22 if c['contract']['duration']==30 else 0)
   self.assertEqual(n['typed']['state'][0]['remaining'],999996194284. if c['contract']['duration']==30 else 999999971590.)
   self.assertFalse(v['full_character_verified']);self.assertFalse(v['in_game_rules_verified'])
 def test_native_scope_restores_calculator_and_heal_methods_on_failure(self):
  from calculator import timeline,buff_manager
  import destructible_damage_policy
  pointers=(timeline.calc_damage,timeline.simulate,timeline.BuffManager,timeline.HitEvent,timeline.CharState._fire,buff_manager.BuffManager.apply_shared_body_heal)
  with patch.object(destructible_damage_policy,'calculate',side_effect=RuntimeError('injected scalar failure')):
   with self.assertRaisesRegex(RuntimeError,'injected'):a.observe(a.fixtures()[0])
  self.assertEqual(pointers,(timeline.calc_damage,timeline.simulate,timeline.BuffManager,timeline.HitEvent,timeline.CharState._fire,buff_manager.BuffManager.apply_shared_body_heal))

class WeaponRosterSavedTests(unittest.TestCase):
 def test_previous141_native_and_input_fingerprints_still_exact(self):
  rows,_=a.prior.prepare();g=json.loads((ROOT/'research/portable-destructible-weapon-shield-short-expected.json').read_text())
  for (name,w,domain),expected in zip(rows,g['entries'],strict=True):
   from portable_removed_sources import REMOVED_SOURCES
   if name in REMOVED_SOURCES:continue
   with self.subTest(name=name):
    self.assertEqual(name,expected['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),expected['input_sha256'])
    self.assertEqual(a.cross.digest(dict(status=64) if domain is None else a.prior.native_reference(domain)),expected['native_sha256'])
 @historical_reference
 def test_actual_original_roster_readback_rejects_hp_ammo_and_typed_corruption(self):
  from portable_backend import source_hashes
  f=json.loads((ROOT/'tests/fixtures/portable-destructible-weapon-rosters-raw.json').read_text());rows,_=a.prepare()
  from portable_destructible_roster_skill_source_contract import verify_retained_sources
  verify_retained_sources(ROOT,'gpu/destructible_weapon_shield_entry.slang',f['source_sha256'])
  self.assertEqual(f['source_sha256'],json.loads((ROOT/'research/portable-destructible-weapon-shield-short-expected.json').read_text())['source_sha256'])
  for record in f['records']:
   name,w,domain=rows[record['index']];self.assertEqual(name,record['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),record['input_sha256'])
   block=array.array('I',[0])*f['output_words']
   for at,value in record['nonzero']:block[at]=value
   self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256']);a.compare(block,domain)
   # Final battle prefix and typed receipt/time must both be audited.
   offsets=(0,L['HEALTH_QUERY_BASE'],L['COMBAT_QUERY_BASE'],L['DAMAGE_ACCOUNTING_QUERY_BASE']+20,787460,790004,790008,790020,790022)
   for at in offsets:
    bad=array.array('I',block);bad[at]^=1
    with self.subTest(name=name,offset=at),self.assertRaises(AssertionError):a.compare(bad,domain)

if __name__=='__main__':unittest.main()
