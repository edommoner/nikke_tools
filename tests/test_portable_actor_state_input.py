"""Typed predicate inputs are literal;life and query scope are GPU-owned."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('named_input',ROOT/'research/verify-world-actor-state.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
from portable_specs import LIMITS as L
from portable_actor_state_specs import append_queries,MAGIC
from calculator.boss_pattern import BossScript
class StateInput(unittest.TestCase):
 def setUp(self):self.case=next(c for c in d.fixtures() if c['name']=='128-typed-predicates-canonical-keys')
 def test_128_pack_without_native_tick_target_selection_or_registry_lookup(self):
  before=copy.deepcopy(self.case)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU life input')),patch.object(BossScript,'resolve_enemies',side_effect=AssertionError('No CPU target set input')):w,m,b=d.compile_case(self.case)
  self.assertEqual(self.case,before);self.assertEqual(len(b),128);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],MAGIC)
 def test_explicit_queries_keep_unknown_identity_and_stale_generation(self):
  w,m,b=d.compile_case(self.case);q=[w[L['COMMAND_BASE']+i*8:L['COMMAND_BASE']+(i+1)*8] for i in range(w[2]) if w[L['COMMAND_BASE']+i*8]==41]
  self.assertEqual([x[3:7] for x in q],[list(x[:4]) for x in self.case['state_queries']]);self.assertEqual(q[1][5],127);self.assertEqual(q[2][6],2)
 def test_query_names_are_opaque_literal_ids_not_cpu_presence(self):
  c=next(c for c in d.fixtures() if c['name']=="opaque-target-name-'a:b: :名前'");w,m,_=d.compile_case(c)
  for i in range(w[2]):
   if w[L['COMMAND_BASE']+i*8]==41:self.assertEqual(w[L['WORLD_ACTOR_STATE_INPUT_BASE']+i*2:L['WORLD_ACTOR_STATE_INPUT_BASE']+i*2+2],[m['states']['a:b: :名前'],0])
 def test_field_contract_keeps_state_policy_reserved_and_old_stride(self):
  w,_,_=d.fields.compile_case(d.fields.fixtures()[0]);self.assertEqual(len(w),92208);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],0);self.assertEqual(w[0],0x50455678)
 def test_query_capacity_rejected_before_command_table_growth(self):
  w,m,_=d.compile_case(self.case);before=list(w)
  with self.assertRaisesRegex(ValueError,'capacity'):append_queries(w,m,[self.case['state_queries'][0]]*64,.5)
  self.assertEqual(w,before)
 def test_query_generation_must_be_authored_positive_integer(self):
  for generation in (0,-1,True,2**31):
   w,m,_=d.compile_case(self.case)
   with self.subTest(generation=generation),self.assertRaises(ValueError):append_queries(w,m,[(0,5,0,generation,'mark')],.5)
 def test_layout_preserves_every_normal_and_field_output_word(self):
  self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS'],L['WORLD_ACTOR_FIELDS_OUTPUT_WORDS']),(86016,159744,262144));self.assertEqual(L['WORLD_ACTOR_STATE_INPUT_BASE'],92208);self.assertEqual(L['WORLD_ACTOR_STATE_INPUT_WORDS'],92336);self.assertEqual(L['WORLD_ACTOR_STATE_ABI'],0x50455679)
 def test_unused_sidecar_remains_zero_and_named_queries_follow_fields(self):
  c=copy.deepcopy(self.case);c['field_queries']=[(0,0,0,1)];w,m,_=d.compile_case(c);self.assertEqual(m['actor_state_query_indices'],[1,2,3])
  for i in range(64):
   if i>=w[2] or w[L['COMMAND_BASE']+i*8]!=41:self.assertEqual(w[L['WORLD_ACTOR_STATE_INPUT_BASE']+i*2:L['WORLD_ACTOR_STATE_INPUT_BASE']+(i+1)*2],[0,0])
if __name__=='__main__':unittest.main()
