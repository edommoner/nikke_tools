import importlib.util,sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects
from gpu_selector import Cuda,probe
spec=importlib.util.spec_from_file_location('predicate_regression',ROOT/'scripts/verify-predicates-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class PredicateCompilerTests(unittest.TestCase):
 def test_defense_and_persona_are_preserved_as_runtime_data(self):
  chars=v.oracle.characters(v.NAMES)
  p=compile_effects(chars,[(v.E('def','buff','def_pct',40),v.NAMES[0]),(v.E('persona','buff','persona_state',1),v.NAMES[0]),(v.E('below','buff','atk_pct',10,'allies_below_def'),v.NAMES[0])])
  self.assertEqual(p['effects'][0][1:3],[0,2]);self.assertEqual(p['effects'][1][213],1);self.assertEqual(p['effects'][2][4],14)
 def test_static_code_matches_unknown_and_runtime_gate_stays_distinct(self):
  chars=v.oracle.characters(v.NAMES);chars[0]['_detail_enemy_code']='풍압'
  es=[(v.E('code','buff','atk_pct',10,condition=['target_code:전격']),v.NAMES[0]),(v.E('boss','buff','atk_pct',10,condition=['target_is_add']),v.NAMES[0])]
  p=compile_effects(chars,es);self.assertEqual(p['effects'][0][15:18],[22,0,0]);self.assertEqual(p['effects'][1][15:18],[25,0,0])
  del chars[0]['_detail_enemy_code'];self.assertEqual(compile_effects(chars,es)['effects'][0][17],1)
class PredicateGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_authored_defense_persona_stun_and_enemy_squads(self):
  cases=v.verify(self.device,include_real=False)
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
