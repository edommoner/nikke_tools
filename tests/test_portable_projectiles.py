"""Native numeric/order contracts and shared all-definition input boundaries."""
import copy,importlib.util,math,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from world_projectile_cases import fixtures
from world_projectile_native import observe
from portable_runtime import validate_effect,UnsupportedPortable
from portable_projectile_specs import STATS,ABI,MODE
from portable_projectile_roster_input import compile_projectile_battle
from portable_specs import LIMITS as L
import portable_backend
import engine_worker
from detail_coverage import body_for

class ProjectileContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={c['name'].removeprefix('projectile-'):c for c in fixtures()}
 def shots(self,name):return [s for s in observe(copy.deepcopy(self.rows[name]))[0]['projectile_shots'] if s['owner']==0]
 def test_additive_rounding_ties_to_even_and_large_negative_clamp(self):
  expected={'-1e+200':1,'-4':1,'-2.5':1,'-1.5':1,'-0.5':3,'0.5':3,'1.5':5,'2.5':5,'5':8}
  for value,count in expected.items():
   with self.subTest(value=value):self.assertEqual(self.shots('add-'+value)[0]['pellets'],count)
 def test_fixed_positive_overrides_additive_but_zero_and_negative_fall_back(self):
  for value,count in {'-2':7,'0':7,'0.1':1,'0.5':1,'1.5':2,'2.5':2,'3.5':4}.items():
   with self.subTest(value=value):self.assertEqual(self.shots('fixed-'+value)[0]['pellets'],count)
 def test_sum_then_round_and_stack_then_round(self):
  self.assertEqual(self.shots('fixed-sum-before-round')[0]['pellets'],2)
  self.assertEqual([s['pellets'] for s in self.shots('same-name-stack')][:4],[3,3,4,5])
 def test_expiry_and_child_effect_change_next_shot(self):
  self.assertEqual([s['pellets'] for s in self.shots('finite-expiry')][:3],[5,5,3])
  self.assertEqual(self.shots('child-cannot-resplit-current-shot')[0]['pellets'],3)
  self.assertEqual(self.shots('child-cannot-resplit-current-shot')[1]['pellets'],6)
 def test_auto_and_charge_have_different_ammo_snapshot_order(self):
  self.assertEqual(self.shots('counted-ammo-before-auto-snapshot')[0]['pellets'],4)
  self.assertEqual([s['pellets'] for s in self.shots('counted-ammo-after-charge-snapshot')],[3,4])
  self.assertEqual(self.shots('charge-snapshot-full_charge')[0]['pellets'],4)
 def test_bare_squad_index_is_inactive_alone_but_matches_inside_counted_effect(self):
  self.assertEqual(self.shots('ammo-callback-before-auto-snapshot')[0]['pellets'],3)
  self.assertEqual(self.shots('mixed-ammo-2-squad_ammo_consume:4')[0]['pellets'],4)
  self.assertEqual(self.shots('mixed-ammo-3-squad_ammo_consume:3')[0]['pellets'],5)
  self.assertEqual([x['pellets'] for x in self.shots('mixed-ammo-2-on_attack')][:2],[3,4])
 def test_exact_reach_threshold_and_explosion_priority(self):
  for family,low,high in [('pierce',1,2),('explosion',3,4),('both',3,4)]:
   value=100-1e-9;below=math.nextafter(value,-math.inf)
   self.assertEqual(self.shots('range-'+family+'-'+below.hex())[0]['reach'],low)
   self.assertEqual(self.shots('range-'+family+'-'+value.hex())[0]['reach'],high)
 def test_dynamic_parts_route_team_notifications_per_frame(self):
  native=observe(copy.deepcopy(self.rows['parts-overlay-delayed-open-close']))[0]
  first=[r for r in native['team_hits'] if r['owner']==0]
  self.assertEqual(first[0]['event'],45)
  self.assertIn(44,[r['event'] for r in first])
  self.assertEqual(first[-1]['event'],45)
  native=observe(copy.deepcopy(self.rows['last-part-death-keeps-current-frame-parts']))[0]
  zero=[r for r in native['team_hits'] if r['time']==0]
  later=[r for r in native['team_hits'] if r['time']>0]
  self.assertTrue(all(r['event']==44 for r in zero))
  self.assertTrue(all(r['event']==45 for r in later))
 def test_modifiers_require_combat_world(self):
  for stat in STATS:
   e=dict(name=stat,type='buff',stat=stat,fixed_value=1,target='self',trigger=dict(timing=['battle_start'],condition=[]))
   with self.assertRaises(UnsupportedPortable):validate_effect(e)
   with self.assertRaises(UnsupportedPortable):validate_effect(e,combat={})
   validate_effect(e,combat={},world_frame=True)
 def test_real_complete_preparation_has_no_battle_or_gpu_input(self):
  p=engine_worker.evaluate(dict(body_for(['라플라스','미란다','도라','N102','메어리'],3),burst_gauge_mode='accumulate',_portable_static_inputs=True));before=copy.deepcopy(p)
  from calculator import timeline
  with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle')),patch.object(timeline.CharState,'tick',side_effect=AssertionError('No CPU ticks')),patch.object(portable_backend,'execute',side_effect=AssertionError('No GPU')),patch.object(portable_backend,'build',side_effect=AssertionError('No build')):w,m=compile_projectile_battle(p)
  self.assertEqual(p,before);self.assertEqual((w[0],w[L['TARGET_COUNTER_INPUT_BASE']+6]),(ABI,MODE));self.assertEqual(len(w),104400);self.assertEqual(m['real_prepared_input']['prepared_effects'],len(p['effects']));self.assertTrue(m['real_prepared_input']['all_character_effects_included']);self.assertFalse(m['real_prepared_input']['cpu_battle_executed'])

if __name__=='__main__':unittest.main()
