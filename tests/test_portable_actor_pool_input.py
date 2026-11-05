"""Authored HP/set input must not contain native battle transitions."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('pool_driver',ROOT/'research/verify-world-actor-pools.py');driver=importlib.util.module_from_spec(s);s.loader.exec_module(driver)
from calculator.boss_pattern import BossScript,validate
from portable_actor_specs import compile_registry
from portable_actor_pool_specs import compile_pools,number
from portable_specs import LIMITS as L
class PoolInput(unittest.TestCase):
 def test_128_pools_pack_without_native_tick_or_hp_land(self):
  c=next(c for c in driver.fixtures() if c['name']=='128-actors-live-127-adds');before=copy.deepcopy(c)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU state as input')),patch.object(BossScript,'hit_add',side_effect=AssertionError('No CPU damage as input')):words,meta,rows=driver.compile_case(c)
  self.assertEqual(c,before);self.assertEqual(len(rows),128);self.assertEqual(len(words),92208);self.assertEqual(words[L['WORLD_ACTOR_POOL_INPUT_BASE']:L['WORLD_ACTOR_POOL_INPUT_BASE']+2],[0x57485031,128])
 def test_cleared_has_no_authored_cpu_death_schedule(self):
  c=next(c for c in driver.fixtures() if c['name']=='gpu-cleared-reopens-generations');words,_,_=driver.compile_case(c)
  self.assertEqual(words[L['WORLD_FRAME_INPUT_BASE']+16+1]&2,2)
 def test_pool_quantities_remain_binary64(self):
  p=validate([dict(id='part',kind='parts',targets=[dict(name='part',hp=9007199254740991,score=7,emit_on_destroy=['event:part_destroy'])])]);_,rows=compile_registry(p,pools=True);w=compile_pools(p,rows)
  self.assertEqual(w[8+12+2:8+12+4],number(9007199254740991));self.assertEqual(w[8+12+6:8+12+9],[1,1,7])
 def test_nonfinite_literal_quantities_rejected(self):
  for v in (float('inf'),float('nan')):
   with self.assertRaises(ValueError):number(v)
 def test_source_attack_adapter_stays_closed(self):
  for p in [dict(id='wave',kind='summon',spec=dict(count=1,hp=3,attack=dict(atk=10,coeff=100,target='all')))]:
   with self.assertRaises(ValueError):compile_registry(validate([p]),pools=True)
 def test_wide_state_fits_transport_without_mutating_normal_layout(self):
  self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS']),(86016,159744));self.assertLessEqual(L['WORLD_ACTOR_POOL_OUTPUT_WORDS'],262144);self.assertEqual(L['WORLD_ACTOR_SETS'],32);self.assertEqual(L['WORLD_ACTOR_SET_WORDS'],520)
if __name__=='__main__':unittest.main()
