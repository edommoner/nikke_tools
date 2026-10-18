import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('accum_bounds',ROOT/'scripts/verify-damage-accum.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
g=m.g
class DamageAccumBoundaryTests(unittest.TestCase):
 def setUp(self):self.chars=m.v.characters(m.N)
 def test_discharge_requires_stored_quantity_reference_without_coefficients(self):
  for ref in (None,'',7,[]):
   with self.subTest(ref=ref),self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.chars,[(m.E('release','damage','accum_split_damage',0,'target',target_effect=ref),m.N[0])])
  for extra in ({'fixed_value':10},{'scaling':'stack_count','scaling_ref':'other'},{'hits_parts':True}):
   effect=m.E('release','damage','accum_split_damage',0,'target',target_effect='pool');effect.update(extra)
   with self.subTest(extra=extra),self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.chars,[(effect,m.N[0])])
 def test_ambiguous_carrier_names_are_not_silently_shared(self):
  effects=[(m.B('pool',stat,100,'target'),m.N[i]) for i,stat in enumerate(m.STATS)]
  with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.chars,effects)
  with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.chars,[(m.B('bad rate','dmg_accum_rate_pct',10,target_effect=[]),m.N[0])])
 def test_forged_carrier_release_and_full_event_fields_reject_before_cuda(self):
  effects=[(m.B('pool',m.STATS[0],100,'target'),m.N[0]),(m.E('release','damage','accum_split_damage',0,'target',event='event:accum_full:pool',target_effect='pool'),m.N[0])]
  p=g.compile_effects(self.chars,effects)
  for row,field,value in [(0,3,-1),(0,3,g.NE),(0,0,.5),(1,36,-1),(1,36,g.NE),(1,36,.5),(1,g.TD+3,-1)]:
   bad=copy.deepcopy(p);bad['effects'][row][field]=value
   with self.subTest(row=row,field=field,value=value),self.assertRaises(ValueError):g.run(None,[bad],[[0,2,124,0,-1,0,0,0]],[[0,0]],[{}])
  for key in (-2,g.NE,.5):
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'accumulation query'):g.run(None,[p],[[0,2,124,0,key,0,0,0]],[[0,0]],[{}])
if __name__=='__main__':unittest.main()
