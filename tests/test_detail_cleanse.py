import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('cleanse_tests',ROOT/'scripts/verify-cleanse-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects,UnsupportedDetail
class CleanseTests(unittest.TestCase):
 def test_limits_are_explicit_and_nonfinite_values_are_rejected(self):
  chars=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':v.v.c.a.META[n]} for n in v.v.NAMES]
  for amount in [0,-1,.5,1,2,1e30]:
   row=compile_effects(chars,[(v.v.E('clean','instant','debuff_cleanse',amount,'all_allies'),v.v.NAMES[0])])['effects'][0]
   self.assertEqual(row[1],26);self.assertEqual(row[6],amount)
  for amount in [float('nan'),float('inf'),None,'all']:
   with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(v.v.E('bad','instant','debuff_cleanse',amount),v.v.NAMES[0])])
 def test_complete_squads_and_positive_raw_characters(self):
  d=v.v.c.Cuda()
  try:cases=v.verify(d,'native')
  finally:d.close()
  self.assertEqual(len(cases),52);self.assertTrue(all(r['passed'] for r in cases),[r for r in cases if not r['passed']])
