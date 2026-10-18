import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('infinite_tests',ROOT/'scripts/verify-infinite-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects

class InfiniteAmmoTests(unittest.TestCase):
 def test_presence_boolean_and_unresolved_placeholder_are_compiled(self):
  from detail_coverage import a
  chars=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':a.META[n]} for n in v.NAMES]
  p=compile_effects(chars,[(v.E('infinite','buff','infinite_ammo',0),v.NAMES[0])])
  self.assertEqual(p['effects'][0][2],59)
  p=compile_effects(chars,[(v.E('placeholder','buff','atk_pct',1,event='non_full_charge_fire_count:{0}'),v.NAMES[0])])
  self.assertEqual(p['effects'][0][151],2)
 def test_magazines_reload_cancellation_and_complete_squads(self):
  d=v.c.Cuda()
  try:cases=v.verify(d,'native')
  finally:d.close()
  self.assertTrue(cases)
  self.assertTrue(all(x['passed'] for x in cases),[x for x in cases if not x['passed']])

if __name__=='__main__':unittest.main()
