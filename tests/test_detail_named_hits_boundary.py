import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('named_hit_boundaries',ROOT/'scripts/verify-named-hits.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
g=m.g
class NamedHitBoundaryTests(unittest.TestCase):
 def setUp(self):self.chars=m.v.characters(m.N)
 def test_named_threshold_rejects_malformed_or_ambiguous_forms(self):
  for timing in ('hit_count::1','hit_count:7:1','hit_count:skill:1:extra','hit_count:skill:bad','hit_count:skill:{0}'):
   with self.subTest(timing=timing),self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.chars,[(m.B('listener','atk_pct',10,event=timing,trigger_values={'10':1}),m.N[0])])
 def test_forced_slot_is_required_and_not_allowed_on_other_operations(self):
  for slot in (None,'','스킬9',7):
   with self.subTest(slot=slot),self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.chars,[(m.E('force','instant','force_skill_use',0,target_skill=slot),m.N[0])])
  with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.chars,[(m.B('not force','atk_pct',10,target_skill='스킬1'),m.N[0])])
if __name__=='__main__':unittest.main()
