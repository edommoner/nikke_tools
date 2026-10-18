import unittest,json,sys,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,UnsupportedDetail
from gpu_selector import Cuda,probe
spec=importlib.util.spec_from_file_location('gauge_regression',ROOT/'scripts/verify-gauge-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class DetailedGaugeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=probe()
  if not p['available']:raise unittest.SkipTest(p['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_gauges_finite_passives_ammo_and_independent_full_squads(self):
  r=v.verify(self.device);self.assertTrue(r['passed'],json.dumps([c for c in r['cases'] if not c['passed']],ensure_ascii=True))
  self.assertEqual(len(r['cases']),14)
  self.assertEqual([e[2] for e in r['cases'][0]['cpu_boundary_events'][:4]],[2,3,4,6])
 def test_invalid_gauge_definitions_fail_closed(self):
  chars=[{'name':n,'_weapon':v.a.META[n]} for n in v.NAMES]
  for e in [v.effect('missing id','instant','gauge_charge',1),v.effect('negative cap','instant','gauge_charge',1,gauge_id='x',gauge_max=-3),v.effect('zero step','buff','atk_pct',1,event='every_stack:x:0'),v.effect('zero mod','buff','atk_pct',1,condition=['gauge_mod:x:0:0']),v.effect('wrong kind','damage','gauge_charge',1,gauge_id='x')]:
   with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(e,v.NAMES[0])])
if __name__=='__main__':unittest.main()
