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
    with v.v.t.raw.injected_effects(e):c=v.a.evaluate({**b,'_compile_gpu_detail':True})
    validate_world(c['program']['world'])
 def test_bad_rows_are_rejected_before_cuda(self):
  n,b,e=next(x for x in v.fixtures() if x[0]=='received-damage-stacks-and-lifetime')
  with v.v.t.raw.injected_effects(e):c=v.a.evaluate({**b,'_compile_gpu_detail':True})
  script=[[0,4,0,0,0,-1,0,0],[0,5,0,0,0,-1,0,0],[0,2,101,0,0,0,0,0]]
  for at,value in [(WB+76,-1),(WB+78,255),(WB+79,2)]:
   p=copy.deepcopy(c['program']);p['world'][at]=value
   with self.assertRaises(ValueError):v.g.run(None,[p],script,[c['enemy']],[c['base_stats']])
 def test_boss_received_damage_is_an_inactive_real_definition(self):
  n,b,e=next(x for x in v.fixtures() if x[0]=='received-damage-stacks-and-lifetime')
  with v.v.t.raw.injected_effects(e):c=v.a.evaluate({**b,'_compile_gpu_detail':True})
  rows=c['program']['boss_effect_rows'];self.assertEqual(set(rows),{'resist','vulnerable'})
  for row in rows.values():
   q=c['program']['effects'][row];self.assertEqual((q[1],q[2],q[4]),(0,12,4));self.assertEqual(q[145],15)

class BossBuffGPU(unittest.TestCase):
 def test_fullburst_end_preserves_random_snapshots_from_end_callbacks(self):
  n,b,e=next(x for x in v.fixtures() if x[0]=='fullburst-end-damage-keeps-query-snapshot')
  d=v.v.Cuda()
  try:r=v.v.compare(d,n,b,e,'native')
  finally:d.close()
  self.assertTrue(r['passed'],r['checks'])
 def test_mode_return_preserves_random_buff_snapshot_after_first_burst(self):
  n,b,e=next(x for x in v.fixtures() if x[0]=='random-caster-ranking-and-world-transitions');b['duration']=30
  d=v.v.Cuda()
  try:r=v.v.compare(d,n+'-past-mode-return',b,e,'native')
  finally:d.close()
  self.assertTrue(r['passed'],r['checks'])
 def test_order_received_damage_and_deferred_cleanse_match_cpu(self):
  d=v.v.Cuda()
  try:rows=[v.v.compare(d,n,b,e,'native') for n,b,e in v.fixtures() if n in ('start-order-not-declaration','received-damage-stacks-and-lifetime','startup-cleanse-deferred-to-next-begin','cleanse-latest-skips-irremovable')]
  finally:d.close()
  self.assertEqual(len(rows),4);self.assertTrue(all(r['passed'] for r in rows))
 def test_shader_semantics_are_identical_when_frame_witnesses_are_disabled(self):
  d=v.v.Cuda()
  try:
   n,b,e=next(x for x in v.fixtures() if x[0]=='random-caster-ranking-and-world-transitions')
   with v.v.t.raw.injected_effects(e):
    witnessed=v.g.evaluate_full(d,v.a.evaluate({**b,'_compile_gpu_detail':True}),module_backend='native')
    b['_debug_boss_frames']=False
    unwitnessed=v.g.evaluate_full(d,v.a.evaluate({**b,'_compile_gpu_detail':True}),module_backend='native')
   for key in ('total_damage','members','burst_timeline','boss_timeline','_random_state'):self.assertEqual(witnessed[key],unwitnessed[key],key)
  finally:d.close()
if __name__=='__main__':unittest.main()
