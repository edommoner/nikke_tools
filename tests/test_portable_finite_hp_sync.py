import json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import engine_worker,reference_health_runtime as health
from portable_health_oracle import observe
class FiniteHealthSynchronization(unittest.TestCase):
 def case(self,stat,owner):
  return dict(name='finite-health-boundary',effects=[dict(name='finite HP',type='buff',stat=stat,target='self',source='스킬1',duration=1,max_stack=1,fixed_value=20,trigger=dict(timing=['battle_start'],condition=[]))],owners=[owner],environment=dict(allies=[dict(base_hp=1000,hp=1000) for _ in range(5)]),script=[[0,0,0,owner,0,-1,0,0],[0,2,0,0,0,0,0,0],[.999,2,0,0,0,1,0,0],[1,2,0,0,0,2,0,0]])
 def test_finite_hp_grant_clamps_current_hp_at_expiration(self):
  for stat in ('max_hp_pct','hp_caster_based_pct'):
   for owner in range(5):
    with self.subTest(stat=stat,owner=owner):
     rows=observe(self.case(stat,owner));self.assertEqual([(q['allies'][owner]['hp'],q['allies'][owner]['max_hp']) for q in rows],[(1200,1200),(1200,1200),(1000,1000)])
 def test_finite_maximum_only_does_not_grant_current_hp(self):
  for stat in ('max_hp_only_pct','hp_only_caster_based_pct'):
   rows=observe(self.case(stat,0));self.assertEqual([(q['allies'][0]['hp'],q['allies'][0]['max_hp']) for q in rows],[(1000,1200),(1000,1200),(1000,1000)])
 def test_finite_lazy_resolution_publishes_derived_percentage(self):
  cases=json.loads((R/'tests/fixtures/portable-lazy.json').read_text())['cases']
  c=next(c for c in cases if c['name']=='lazy-max-hp-first-consumption-and-derived-percentage')
  row=observe(c)[1]['allies'][1];self.assertEqual((row['hp'],row['max_hp'],row['hp_pct']),(200,1100,200/1100*100))
 def test_infinite_plain_hp_keeps_existing_compatibility_policy(self):
  for duration in (-1,None):
   manager=type('Manager',(),{'_effects':[(dict(type='buff',stat='max_hp_pct',duration=duration),'owner')]})()
   self.assertFalse(health.enabled(manager))
if __name__=='__main__':unittest.main()
