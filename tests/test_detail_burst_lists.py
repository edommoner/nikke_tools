import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import weapon_rows,UnsupportedDetail
from detail_coverage import a,body_for

class BurstListCompilerTests(unittest.TestCase):
 def compile(self,cycles):
  body=body_for(['리타','도라','앨리스','모더니아','얀'],1)
  prepare=a.sim.prepare
  def configured(request):
   run=prepare(request);run.config['burst_pattern']={'리타':cycles};return run
  with patch.object(a.sim,'prepare',configured):return a.evaluate({**body,'_compile_gpu_detail':True})
 def test_empty_priority_retains_both_b1_candidates(self):
  compiled=self.compile([]);chars=compiled['program']['chars']
  self.assertEqual(chars[0]['_detail_pattern'],-1)
  self.assertTrue(chars[4]['_detail_burst_candidate'])
 def test_exact_u32_word_boundaries(self):
  cycles=[1,32,33,64,65,96,97,128,129,160]
  compiled=self.compile(cycles);rows=weapon_rows(compiled['program']['chars'],compiled['base_stats'])
  self.assertEqual(rows[35:40],[2147483649]*5)
 def test_invalid_cycle_lists_fail_closed(self):
  for cycles in ([0],[161],[-1],[True],[1.5],['3']):
   with self.subTest(cycles=cycles),self.assertRaises(UnsupportedDetail):self.compile(cycles)
if __name__=='__main__':unittest.main()
