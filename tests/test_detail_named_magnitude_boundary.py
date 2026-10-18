import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
import detail_gpu as g
from effect_spec import NAMED_MAGNITUDE
spec=importlib.util.spec_from_file_location('named_boundary_helpers',ROOT/'scripts/verify-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class NamedMagnitudeBoundaryTests(unittest.TestCase):
 def test_each_registered_modifier_requires_named_reference(self):
  chars=v.characters(['리타','크라운','모더니아','앨리스','N102'])
  for stat in NAMED_MAGNITUDE:
   for ref in (None,'',7,[]):
    with self.subTest(stat=stat,ref=ref),self.assertRaises(g.UnsupportedDetail):
     g.compile_effects(chars,[({'trigger':{'timing':['battle_start'],'condition':[]},'name':'test','type':'buff','stat':stat,'target':'self','target_effect':ref,'fixed_value':10},chars[0]['name'])])
 def test_all_registered_modifiers_compile_to_one_named_reference_contract(self):
  chars=v.characters(['리타','크라운','모더니아','앨리스','N102'])
  for stat,code in NAMED_MAGNITUDE.items():
   p=g.compile_effects(chars,[({'trigger':{'timing':['battle_start'],'condition':[]},'name':'test','type':'buff','stat':stat,'target':'self','target_effect':'shared','fixed_value':10},chars[0]['name'])])
   row=p['effects'][0];self.assertEqual((row[1],row[2],row[36]),(0,code,p['states']['shared']))
if __name__=='__main__':unittest.main()
