import copy,importlib.util,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_mode_enemy_name_oracle import observe
from portable_runtime import UnsupportedPortable
s=importlib.util.spec_from_file_location('domain_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
CASES=json.loads((R/'tests/fixtures/portable-mode-enemy-names.json').read_text())['cases']
class ModeEnemyDomains(unittest.TestCase):
 def test_exact_names_definition_orders_and_enemy_routes_compile(self):
  self.assertEqual(len(CASES),24)
  for c in CASES:
   with self.subTest(case=c['name']):v.compile_case(c)
 def test_physical_native_damage_persists_after_mode_ends(self):
  for c in CASES:
   with self.subTest(case=c['name']):self.assertEqual([q['damage'][0] for q in observe(c)['queries']],[1500,3900,7500,13500])
 def test_same_name_ally_buff_is_still_rejected(self):
  c=copy.deepcopy(CASES[0]);c['effects'][1].update(target='self',stat='atk_pct')
  with self.assertRaisesRegex(UnsupportedPortable,'Multiple named non-buff'):v.compile_case(c)
 def test_two_modes_or_unnamed_domain_aliases_are_still_rejected(self):
  for kind in ('two_modes','unnamed'):
   c=copy.deepcopy(CASES[0])
   if kind=='two_modes':c['effects'].insert(1,copy.deepcopy(c['effects'][0]))
   else:
    for e in c['effects'][:2]:e['name']=''
    c['effects'][1]['trigger']['condition']=[]
   with self.subTest(kind=kind),self.assertRaisesRegex(UnsupportedPortable,'Multiple named non-buff'):v.compile_case(c)
if __name__=='__main__':unittest.main()
