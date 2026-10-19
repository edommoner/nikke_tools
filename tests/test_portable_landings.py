"""Static receipt policy, native HP cache invalidation, and queue contracts."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import LIMITS as L
from portable_landing_oracle import observe
sp=importlib.util.spec_from_file_location('vland',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
CASES=json.loads((ROOT/'tests/fixtures/portable-landings.json').read_text())['cases']
def compilable():
 c=copy.deepcopy(CASES[0])
 for e in c['effects']:
  if e.get('stat')=='lifesteal_pct':e['stat']='crit_dmg'
 return c
class LandingTests(unittest.TestCase):
 def test_policy_and_flush_are_static_not_cpu_receipt_input(self):
  c=compilable();before=copy.deepcopy(c);words,meta=v.compile_case(c);at=L['LANDING_META_BASE'];self.assertEqual(words[at:at+8],[1,0,0,0,0,0,0,0]);self.assertTrue(meta['native_landing']);self.assertEqual(c,before)
  command=L['COMMAND_BASE']+8;self.assertEqual(words[command],30);self.assertEqual(words[command+3:command+8],[0]*5)
 def test_native_policy_and_flush_are_validated_before_gpu(self):
  for value in (1,None,'native',-1):
   c=compilable();c['environment']['native_landing']=value
   with self.subTest(value=value),self.assertRaises(ValueError):v.compile_case(c)
  for field,value in ((2,1),(3,1),(4,1),(5,0),(6,1),(7,1)):
   c=compilable();c['script'][1][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):v.compile_case(c)
  c=compilable();c['environment']['native_landing']=False
  with self.assertRaises(ValueError):v.compile_case(c)
 def test_native_cache_rechecks_rate_after_same_timestamp_hp_change(self):
  c=next(c for c in CASES if c['name']=='landing-rate-rechecks-current-hp-per-receipt');r=observe(c)
  self.assertEqual(r['queries'][0]['allies'][0]['hp'],200)
  heals=[e for e in r['history'] if e['event']=='native-body-heal'];self.assertEqual([e['amount'] for e in heals],[50,50])
 def test_hand_timeline_expectations_cover_every_authored_case(self):
  for c in CASES:
   with self.subTest(name=c['name']):v.contains(observe(c)['queries'],c['expected_queries'])
 def test_b3_callback_keeps_a_new_pending_batch(self):
  c=next(c for c in CASES if c['name']=='landing-b3-child-pending-survives-parent-drain');r=observe(c)
  self.assertEqual(r['queries'][0]['pending_burst']['count'],1);self.assertEqual(r['queries'][0]['allies'][2]['hp'],250)
if __name__=='__main__':unittest.main()
