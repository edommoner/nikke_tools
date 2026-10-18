import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('gauge_tests',ROOT/'scripts/verify-burst-gauge-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class BurstGaugeCompilerTests(unittest.TestCase):
 def test_mode_is_validated_and_reaches_the_gpu_configuration(self):
  body=v.c.body_for(v.NAMES,1,True)
  for mode in ('fixed','accumulate'):
   compiled=v.c.a.evaluate({**body,'burst_gauge_mode':mode,'_compile_gpu_detail':True})
   self.assertEqual(compiled['prepared'].config['burst_gauge_mode'],mode)
   self.assertTrue(all(c['_detail_gauge_mode']==(mode=='accumulate') for c in compiled['program']['chars']))
  with self.assertRaises(ValueError):v.c.a.evaluate({**body,'burst_gauge_mode':'unknown'})

class BurstGaugeGPUTests(unittest.TestCase):
 def test_actual_gauge_and_complete_squads_match_independent_cpu(self):
  d=v.c.Cuda()
  try:cases=v.verify(d,'native')
  finally:d.close()
  self.assertTrue(cases)
  self.assertTrue(all(c['passed'] for c in cases),[c for c in cases if not c['passed']])

if __name__=='__main__':unittest.main()
