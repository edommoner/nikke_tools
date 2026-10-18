import importlib.util,sys,unittest,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,UnsupportedDetail,run
from gpu_selector import Cuda,probe
spec=importlib.util.spec_from_file_location('lists_regression',ROOT/'scripts/verify-lists-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class ListCompilerTests(unittest.TestCase):
 def test_identical_plans_share_inert_rows_without_splitting_effect_identity(self):
  p=compile_effects(v.oracle.characters(v.NAMES),[(v.E(n,'buff','atk_pct',1,['self','allies_top_atk_excl:1']),v.NAMES[0]) for n in ('one','two')])
  self.assertEqual(len(p['effects']),4);self.assertEqual(p['effects'][0][5],2);self.assertEqual(p['effects'][1][5],2)
  self.assertEqual([r[58] for r in p['effects'][:2]],[0,1]);self.assertTrue(all(r[1]==-1 and r[144]==0 for r in p['effects'][2:]))
 def test_list_bounds_reject_instead_of_truncating_and_empty_lists_compile(self):
  chars=v.oracle.characters(v.NAMES)
  for targets in (['self']*22,['enemy','self']):
   with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(v.E('large','buff','atk_pct',1,targets),v.NAMES[0])])
  p=compile_effects(chars,[(v.E('empty','buff','atk_pct',1,[]),v.NAMES[0])]);self.assertEqual(len(p['effects']),1);self.assertEqual(p['effects'][0][48],0)
 def test_corrupt_list_references_rejected_before_gpu_execution(self):
  p=compile_effects(v.oracle.characters(v.NAMES),[(v.E('list','buff','atk_pct',1,['self']),v.NAMES[0])]);p['effects'][0][5]=127
  with self.assertRaisesRegex(ValueError,'target list'):run(None,[p],[],[[1,1]],[{}])
class ListGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_order_duplicates_eager_ranks_and_complete_squads(self):
  cases=v.verify(self.device,include_real=False)
  self.assertTrue(all(c['passed'] for c in cases),str([c for c in cases if not c['passed']]))
class ListCpuLoggingTests(unittest.TestCase):
 def test_list_logging_keeps_target_identity_and_nested_events(self):
  from calculator.buff_manager import BuffManager
  class BM(BuffManager):
   def _register_all(self):self._effects=[];self._build_notify_index()
  bm=BM(v.oracle.characters(v.NAMES));logs=[];seen=[]
  bm.register_instant_event_handler(lambda *args:logs.append(args))
  targets=[v.NAMES[1],v.NAMES[0],v.NAMES[1]]
  outer=v.E('outer','instant','heal_hp_pct',1,targets);inner=v.E('inner','instant','heal_hp_pct',2,'self')
  def handler(eff,caster,t,val):
   seen.append(bm._resolve_target(eff['target'],caster))
   if eff is outer:bm._dispatch_instant(inner,caster,t)
  bm.register_instant_handler('heal_hp_pct',handler);bm._dispatch_instant(outer,v.NAMES[0],.1)
  self.assertIs(outer['target'],targets);self.assertEqual(seen,[targets,[v.NAMES[0]]]);self.assertEqual([log[0] for log in logs],['outer','inner']);self.assertEqual(logs[0][2],v.NAMES[0])
 def test_install_is_idempotent_and_string_lookup_is_preserved(self):
  import engine_compat
  from calculator.buff_manager import BuffManager
  before=BuffManager.__init__;engine_compat.install();self.assertIs(before,BuffManager.__init__)
  names=engine_compat.CharacterLookup({v.NAMES[0]:1});self.assertIn(v.NAMES[0],names);self.assertNotIn([v.NAMES[0]],names);self.assertEqual(names[v.NAMES[0]],1)
if __name__=='__main__':unittest.main()
