"""Compilation validation for named removal and prefix duration extension."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,UnsupportedDetail,EXTEND_MASK,MASK_WORDS
spec=importlib.util.spec_from_file_location('named_validator',ROOT/'scripts/verify-named-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class NamedEffectCompilerTests(unittest.TestCase):
 def compile(self,effects):return compile_effects(v.oracle.characters(v.NAMES),[(e,v.NAMES[0]) for e in effects])
 def test_prefix_state_masks_cover_high_words_and_exact_boundary(self):
  es=[v.effect('filler '+str(i),'buff','crit_dmg',0) for i in range(98)]
  es += [v.effect('mode','buff','atk_pct',10),v.effect('mode 2','buff','atk_pct',20),v.effect('mode2','buff','atk_pct',40),v.effect('extend','instant','named_buff_duration_extend',1,target_effect='mode')]
  p=self.compile(es);q=p['effects'][-1];words=[int(q[i]) for i in range(EXTEND_MASK,EXTEND_MASK+MASK_WORDS)]
  for name in ('mode','mode 2'):i=p['states'][name];self.assertTrue(words[i//32]&(1<<(i%32)))
  i=p['states']['mode2'];self.assertFalse(words[i//32]&(1<<(i%32)))
 def test_invalid_scope_or_reference_is_not_silently_accepted(self):
  for kind,stat,kw in [('instant','remove_named_buff',{'target_effect':'x','remove_scope':'nearby'}),('buff','atk_pct',{'remove_scope':'target'}),('instant','remove_named_buff',{'target_effect':7}),('instant','named_buff_duration_extend',{'target_effect':None})]:
   with self.subTest(kind=kind,stat=stat,kw=kw),self.assertRaises(UnsupportedDetail):self.compile([v.effect('bad',kind,stat,1,**kw)])
 def test_unregistered_name_cleanup_is_compiled_as_noop(self):
  p=self.compile([v.effect('cleanup','instant','remove_named_buff',0,'all_allies',target_effect='missing')]);self.assertEqual(p['effects'][0][1],1)
class NamedEffectGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from gpu_selector import Cuda,probe
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_state_changes_and_complete_squads_match_independent_cpu(self):
  import json
  cases=v.verify(self.device)
  self.assertGreaterEqual(len(cases),len(v.primitives())+len(v.full_scenarios()))
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
