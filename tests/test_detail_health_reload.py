"""HP conversion and reload semantics use the independent upstream oracle."""
import sys,json,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('health_reload_regression',ROOT/'scripts/verify-health-reload-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects,run,UnsupportedDetail
from gpu_selector import Cuda,probe
class HealthReloadCompilerTests(unittest.TestCase):
 def test_special_values_remain_separate_from_generic_stat_routing(self):
  es=[v.E('HP conversion','buff','atk_from_hp_pct',2),v.E('fixed reload','buff','reload_time_fixed',.3),v.E('forced reload','instant','force_reload',0)]
  rows=compile_effects(v.oracle.characters(v.NAMES),[(e,v.NAMES[0]) for e in es])['effects']
  self.assertEqual([(q[1],q[241],q[242]) for q in rows],[(4,1,0),(4,0,1),(23,0,0)])
  for stat in ['atk_flat','enemy_def_down_pct','enemy_def_down_flat']:
   with self.assertRaises(UnsupportedDetail):compile_effects(v.oracle.characters(v.NAMES),[(v.E('internal field','buff',stat,1),v.NAMES[0])])
class HealthReloadGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=probe()
  if not p['available']:raise unittest.SkipTest(p['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_primitives_and_complete_squads(self):
  cases=v.verify(self.device,'native',False)
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
 def test_forced_reload_matches_each_frame_including_interrupted_instant_charge(self):
  for label,definitions,seconds in v.full_scenarios():
   if label not in ['force-reload-base-2','last-fire-can-interrupt-instant-charge','zero-fixed-reload-at-battle-start','force-at-full-charge-still-fires']:continue
   with self.subTest(case=label):
    chars=v.oracle.characters(v.NAMES);effects=[(e,n) for n,es in definitions.items() for e in es];program=v.oracle.program(chars,effects);who=2
    bs={n:{'atk':100000+i*1234,'def':1000,'hp':1000000} for i,n in enumerate(v.NAMES)}
    script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
    for frame in range(seconds*60):
     t=frame/60;script.extend([[t,3,0,who,0,-1,0,0],[t,2,0,who,-1,frame,0,0]])
    cpu,totals=v.oracle.oracle(program,script,[31784,17],bs,True,True);gpu=run(self.device,[program],script,[[31784,17]],[bs])
    for frame,(x,y) in enumerate(zip(cpu,gpu['queries'][0])):
     for k in [38,39,40,41,42,44,47]:self.assertEqual(x[k],y[k],(label,frame,k,x[k],y[k]))
    self.assertEqual(totals,gpu['totals'][0])
if __name__=='__main__':unittest.main()
