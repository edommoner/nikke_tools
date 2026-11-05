"""Scope input packing contains no CPU-selected enemies or mutation results."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('mutation_input',ROOT/'research/verify-world-actor-mutation.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
from calculator.boss_pattern import BossScript
from portable_specs import LIMITS as L
class MutationInput(unittest.TestCase):
 def test_pack_does_not_tick_resolve_or_mutate_authored_case(self):
  c=next(c for c in d.fixtures() if c['name']=='128-scope-no-mask-alias');before=copy.deepcopy(c)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU life')),patch.object(BossScript,'resolve_enemies',side_effect=AssertionError('No CPU scope')):w,m,b=d.compile_case(c)
  self.assertEqual(c,before);self.assertEqual(len(b),128);self.assertEqual(w[0],L['WORLD_ACTOR_MUTATION_ABI']);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],d.MAGIC)
 def test_all_enemy_scope_uses_literal_128_limit(self):
  c=d.fixtures()[2];w,m,b=d.compile_case(c);at=L['DAMAGE_DEFINITION_BASE']+8;self.assertEqual(w[at:at+2],[2,128])
 def test_ranked_scope_keeps_literal_65_count(self):
  c=next(c for c in d.fixtures() if c['name']=='128-scope-no-mask-alias');w,m,b=d.compile_case(c);self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+8:L['DAMAGE_DEFINITION_BASE']+10],[9,65])
 def test_global_scope_has_no_enemy_selector_payload(self):
  c=next(c for c in d.fixtures() if c['name']=='global-name-ignores-selector-boss');w,m,b=d.compile_case(c);self.assertEqual(w[L['DEFINITION_BASE']+2*32+21],0);self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+16:L['DAMAGE_DEFINITION_BASE']+24],[0]*8)
 def test_prior_state_input_wire_unchanged(self):
  c=d.state.fixtures()[0];w,m,b=d.state.compile_case(c);self.assertEqual(w[0],0x50455679);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],0x57533031);self.assertEqual(len(w),92336)
 def test_named_scope_sidecars_keep_opaque_state_id(self):
  c=next(c for c in d.fixtures() if c['name']=='opaque-colon-unicode-name');w,m,b=d.compile_case(c);self.assertEqual(w[L['DEFINITION_BASE']+32+18],m['states']['a:b:名前'])
 def test_negative_scope_is_target_word(self):
  rows,programs,bad=d.prepare();w=dict(bad)['removal-scope-overflow'];self.assertEqual(w[L['DEFINITION_BASE']+32+21],3)
 def test_no_new_input_or_output_stride(self):
  self.assertEqual(L['WORLD_ACTOR_MUTATION_ABI'],0x5045567a);self.assertEqual(L['WORLD_ACTOR_STATE_INPUT_WORDS'],92336);self.assertEqual(L['WORLD_ACTOR_FIELDS_OUTPUT_WORDS'],262144)
if __name__=='__main__':unittest.main()
