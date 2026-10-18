import unittest,json,sys,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda,probe
from detail_gpu import compile_effects,UnsupportedDetail
s=importlib.util.spec_from_file_location('periodic_regression',ROOT/'scripts/verify-periodic-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class DetailedPeriodicTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=probe()
  if not p['available']:raise unittest.SkipTest(p['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_full_squad_timer_bullet_boundaries_and_actual_execution(self):
  report=v.verify(self.device)
  self.assertTrue(report['passed'],json.dumps([c for c in report['cases'] if not c['passed']],ensure_ascii=True))
  self.assertEqual(len(report['cases']),17)
 def test_invalid_periodic_and_bullet_modes_fail_closed(self):
  chars=[{'name':n,'_weapon':v.a.META[n]} for n in v.NAMES]
  for e in [v.effect('bad timer','instant','heal_hp_pct',10,tick_interval=-1),v.effect('bad bullet','buff','atk_pct',10,duration_bullets=0),v.effect('not a periodic buff','buff','atk_pct',10,tick_interval=1),v.effect('phase without clock','damage','damage',10,tick_start='immediate')]:
   with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(e,v.NAMES[0])])
if __name__=='__main__':unittest.main()
