"""Boss buff lifecycle must execute on device with no CPU combat precomputation."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('boss_buff_tests',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from detail_boss import WB,BW,validate_world

class BossBuffInputs(unittest.TestCase):
 def test_every_fixture_compiles_without_cpu_combat(self):
  with patch.object(v.a.sim,'execute',side_effect=AssertionError('CPU combat invoked')):
   for n,b,e in v.fixtures():
    with v.v.t.raw.injected_effects(e):c=v.a.evaluate({**b,'_compile_detail':True})
    validate_world(c['program']['world'])
 def test_boss_received_damage_is_an_inactive_real_definition(self):
  n,b,e=next(x for x in v.fixtures() if x[0]=='received-damage-stacks-and-lifetime')
  with v.v.t.raw.injected_effects(e):c=v.a.evaluate({**b,'_compile_detail':True})
  rows=c['program']['boss_effect_rows'];self.assertEqual(set(rows),{'resist','vulnerable'})
  for row in rows.values():
   q=c['program']['effects'][row];self.assertEqual((q[1],q[2],q[4]),(0,12,4));self.assertEqual(q[145],15)

class BossBuffGPU(unittest.TestCase):
    pass
if __name__=='__main__':unittest.main()
