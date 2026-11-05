"""Literal wide recipients preserve one shared interpreter and all128 identities."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('field_input','research/verify-world-actor-fields.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
from calculator.boss_pattern import BossScript
from portable_specs import LIMITS as L
class FieldsInput(unittest.TestCase):
 def test_full128_input_has_no_cpu_advance_damage_or_target_resolution(self):
  c=next(c for c in d.fixtures() if c['name']=='fields-all128-resident-carriers');before=copy.deepcopy(c)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU transition as input')),patch.object(BossScript,'hit_add',side_effect=AssertionError('No CPU HP as input')),patch.object(BossScript,'resolve_enemies',side_effect=AssertionError('No CPU recipient snapshot as input')):words,_,bindings=d.compile_case(c)
  self.assertEqual(c,before);self.assertEqual(len(bindings),128);self.assertEqual(words[L['DAMAGE_DEFINITION_BASE']+1],128);self.assertEqual(words[0],0x50455678)
 def test_rank_uses_literal_attack_quantities(self):
  c=next(c for c in d.fixtures() if c['name']=='rank-enemies_top_atk:2');words,_,_=d.compile_case(c)
  from portable_actor_pool_specs import number
  self.assertEqual(words[L['WORLD_ACTOR_POOL_INPUT_BASE']+2:L['WORLD_ACTOR_POOL_INPUT_BASE']+4],number(114344));self.assertEqual(words[L['WORLD_ACTOR_POOL_DEF_BASE']+12+9:L['WORLD_ACTOR_POOL_DEF_BASE']+12+11],number(114345))
 def test_old_packing_keeps_reserved_fields_zero(self):
  c=d.pool.fixtures()[0];words,_,_=d.pool.compile_case(c)
  self.assertEqual(words[L['WORLD_ACTOR_POOL_INPUT_BASE']+2:L['WORLD_ACTOR_POOL_INPUT_BASE']+8],[0]*6)
 def test_permanent_count_predicate_not_folded_from_initial_population(self):
  c=next(c for c in d.fixtures() if c['name']=='count-delayed-spawn-passive-gates');words,_,_=d.compile_case(c)
  self.assertEqual(words[L['CONDITION_BASE']],40)
 def test_explicit_queries_keep_authored_generation_without_cpu_lookup(self):
  c=next(c for c in d.fixtures() if c['name']=='typed-query-exact-unknown-stale')
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU generations as input')):words,_,_=d.compile_case(c)
  commands=[words[L['COMMAND_BASE']+i*8:L['COMMAND_BASE']+(i+1)*8] for i in range(words[2])];queries=[row for row in commands if row[0]==39]
  self.assertEqual([row[3:7] for row in queries],[list(q) for q in c['field_queries']]);self.assertEqual(queries[-1][6],2)
 def test_output_extensions_do_not_mutate_old_layouts(self):
  self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS'],L['WORLD_ACTOR_POOL_OUTPUT_WORDS']),(86016,159744,253952));self.assertEqual(L['WORLD_ACTOR_FIELDS_OUTPUT_WORDS'],262144);self.assertLessEqual(L['WORLD_ACTOR_FIELD_ALL_BASE']+128*12,262144-16)
if __name__=='__main__':unittest.main()
