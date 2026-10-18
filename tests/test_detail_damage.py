import sys,json,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda,probe
from detail_gpu import compile_effects,UnsupportedDetail
spec=importlib.util.spec_from_file_location('damage_regression',ROOT/'scripts/verify-damage-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class DetailedDamageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=probe()
  if not p['available']:raise unittest.SkipTest(p['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_typed_damage_dynamic_hits_fixed_charge_and_full_squads(self):
  r=v.verify(self.device);self.assertTrue(r['passed'],json.dumps([c for c in r['cases'] if not c['passed']],ensure_ascii=True));self.assertEqual(len(r['cases']),20)
 def test_malformed_new_damage_fields_fail_closed(self):
  cs=[{'name':n,'_weapon':v.a.META[n]} for n in v.NAMES]
  for e in [v.effect('empty suffix','damage','damage:',10),v.effect('too many hits','damage','damage:300',10),v.effect('bad reference','damage','damage',10,hit_count_gauge_ref=5),v.effect('parts is not a bool','damage','damage',10,hits_parts=1),v.effect('fields on buff','buff','atk_pct',10,hits_parts=True)]:
   with self.assertRaises(UnsupportedDetail):compile_effects(cs,[(e,v.NAMES[0])])
if __name__=='__main__':unittest.main()
