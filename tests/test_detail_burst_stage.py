import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('burst_stage_tests',ROOT/'scripts/verify-burst-stage-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects,UnsupportedDetail
class BurstStageTests(unittest.TestCase):
 def test_reentry_and_variable_stage_are_distinct_from_numeric_buffs(self):
  chars=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':v.c.a.META[n]} for n in v.NAMES]
  effects=[v.E('open','instant','burst_reentry',1,event='burst_cast'),v.E('move','buff','burst_stage_override:A',0),v.E('reenter','buff','burst_stage_override:reenter2',0)]
  rows=compile_effects(chars,[(e,v.NAMES[0]) for e in effects])['effects']
  self.assertEqual([r[1] for r in rows],[25,4,4]);self.assertEqual(rows[1][252],4);self.assertEqual(rows[2][253],2)
  with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(v.E('invalid','buff','burst_stage_override:9',0),v.NAMES[0])])
 def test_native_complete_battles(self):
  d=v.c.Cuda()
  try:cases=v.verify(d,'native')
  finally:d.close()
  self.assertTrue(cases);self.assertTrue(all(r['passed'] for r in cases),[r for r in cases if not r['passed']])
