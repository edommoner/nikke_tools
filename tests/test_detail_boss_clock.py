"""Independent boss lifecycle, bytecode rejection and context recovery."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('boss_clock_tests',ROOT/'scripts/verify-boss-clock-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from detail_boss import validate_world,validate_patterns,WP,WB

class BossClockInputTests(unittest.TestCase):
 def test_all_worlds_compile_without_running_cpu_combat(self):
  with patch.object(v.a.sim,'execute',side_effect=AssertionError('CPU combat invoked')):
   for name,body,extra in v.fixtures():
    saved=copy.deepcopy(body)
    with v.t.raw.injected_effects(extra):c=v.a.evaluate({**body,'_compile_detail':True})
    validate_world(c['program']['world']);self.assertEqual(body,saved,name)

class BossClockGPUTests(unittest.TestCase):
    pass
if __name__=='__main__':unittest.main()
