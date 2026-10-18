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
 def test_slot_selection_and_forged_references_are_checked(self):
  effects=[(m.B('selected','atk_pct',10),m.N[0]),(m.B('other owner','atk_pct',10),m.N[1]),(m.E('force','instant','force_skill_use',0,target_skill='스킬1'),m.N[0])]
  effects[-1][0]['source']='스킬2';p=g.compile_effects(self.chars,effects);row=p['effects'][2]
  self.assertEqual(row[g.B3_MASK],1)
  for bits in (2,4,1.5,-1):
   bad=copy.deepcopy(p);bad['effects'][2][g.B3_MASK]=bits
   with self.subTest(bits=bits),self.assertRaises(ValueError):g.run(None,[bad],[[0,2,0,0,-1,0,0,0]],[[0,0]],[{}])
  for event in (55,56):
   with self.subTest(event=event),self.assertRaisesRegex(ValueError,'private skill'):
    g.run(None,[p],[[0,0,event,0,0,-1,0,0],[0,2,0,0,-1,0,0,0]],[[0,0]],[{}])
if __name__=='__main__':unittest.main()
