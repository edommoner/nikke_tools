"""World auto packets use skill modifiers unless the author explicitly opts in."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_specs import LIMITS as L
import world_skill_formula_cases as cases
class WorldSkillFormulaContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={c['name']:c for c in cases.fixtures()}
 def packets(self,name):return cases.suite.inspect_native(self.rows[name])[1]
 def test_native_auto_ignores_normal_bonus_but_explicit_normal_formula_uses_it(self):
  base=self.packets('direct-family-auto_damage')[0]['amount']
  self.assertEqual(self.packets('auto-normal-only-damage')[0]['amount'],base)
  self.assertGreater(self.packets('auto-explicit-normal-damage')[0]['amount'],base)
  self.assertEqual([r['amount'] for r in self.packets('auto-three-normal-only')],[base]*3)
 def test_world_packed_formula_matches_the_author_not_auto_family_name(self):
  for name,c in self.rows.items():
   w,_,_=cases.suite.compile_case(c);row=next(i for i,e in enumerate(c['effects']) if e.get('type')=='damage')
   self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+row*8+3],int(c['effects'][row].get('damage_formula')=='normal_attack'),name)
 def test_native_auto_uses_skill_critical_modifiers(self):
  base=self.packets('direct-family-auto_damage')[0]['amount']
  self.assertEqual(self.packets('auto-normal-only-critical')[0]['amount'],base)
  self.assertGreater(self.packets('auto-skill-critical')[0]['amount'],base)
if __name__=='__main__':unittest.main()
