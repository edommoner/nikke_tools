import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('random_tests',ROOT/'scripts/verify-random-target-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects,UnsupportedDetail

class RandomTargetTests(unittest.TestCase):
 def test_seed_mismatch_rejects_even_an_equal_damage_result(self):
  from gpu_service import resolve_verification
  cpu=dict(total_damage=1,members=[],base_stats={},burst_timeline=[],seed=1)
  gpu={**cpu,'seed':2,'compute':{'backend':'cuda_detail'}}
  result=resolve_verification(gpu,cpu)
  self.assertEqual(result['compute']['backend'],'cpu')
  self.assertFalse(result['compute']['cpu_verification']['seed_equal'])

 def test_shared_seed_validation_and_compiler_target_contract(self):
  body=v.v.v.c.body_for(v.v.v.NAMES,1,True)
  for seed in (None,True,-1,1.5,4294967296,'1'):
   with self.assertRaises(ValueError):v.v.v.c.a.evaluate({**body,'seed':seed,'_compile_gpu_detail':True})
  chars=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':v.v.v.c.a.META[n]} for n in v.v.v.NAMES]
  effects=[(v.E('one','buff','atk_pct',10,'allies_random:2'),v.OWNER),(v.E('two','buff','crit_dmg',10,'allies_random:2'),v.OWNER),(v.E('clean','instant','debuff_cleanse',1,'allies_random_with_debuff:2'),v.OWNER)]
  rows=compile_effects(chars,effects)['effects']
  self.assertEqual(rows[0][4],19);self.assertEqual(rows[2][4],20)
  self.assertEqual(rows[0][257],rows[1][257]);self.assertNotEqual(rows[0][257],rows[2][257])
  with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(v.E('too long','instant','ammo_charge_flat',1,['allies_random_with_debuff:5']*5),v.OWNER)])

 def test_complete_squads_match_damage_and_final_random_state(self):
  device=v.v.v.c.Cuda()
  try:rows=v.verify(device,'native',quick=True)
  finally:device.close()
  self.assertEqual(len(rows),26)
  self.assertTrue(all(r['passed'] for r in rows),[r for r in rows if not r['passed']])

 def test_special_atk_query_targets_follow_time_and_cache_generation(self):
  device=v.v.v.c.Cuda()
  try:rows=sum((v.verify(device,'native',only_case=label) for label in ('caster-atk-special-lazy-target','hp-conversion-special-lazy-target')),[])
  finally:device.close()
  self.assertEqual(len(rows),8)
  self.assertTrue(all(r['passed'] for r in rows),[r for r in rows if not r['passed']])
