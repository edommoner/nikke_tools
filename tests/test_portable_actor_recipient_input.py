"""Persistent capture inputs contain authored definitions,never CPU memberships."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('persistent_input',ROOT/'research/verify-world-actor-recipients.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
from calculator.boss_pattern import BossScript
from portable_specs import LIMITS as L
from portable_backend import execute
class RecipientInput(unittest.TestCase):
 def test_shared128_pack_has_no_cpu_tick_or_target_snapshot(self):
  c=next(c for c in d.fixtures() if c['name']=='one-shared-initialized-carrier-128');before=copy.deepcopy(c)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU clock')),patch.object(BossScript,'resolve_enemies',side_effect=AssertionError('No CPU recipients')):w,m,b=d.compile_case(c)
  self.assertEqual(c,before);self.assertEqual(len(b),128);self.assertEqual(w[0],L['WORLD_ACTOR_RECIPIENT_ABI']);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],d.MAGIC);self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+1],128)
 def test_initializer_binding_is_static_definition_not_recipient_list(self):
  w,m,b=d.compile_case(d.fixtures()[0]);self.assertEqual(w[L['MODE_BASE']+32+4],1);self.assertEqual(len(w),92336)
 def test_prior_mutation_layout_and_policy_remain_reserved(self):
  s=importlib.util.spec_from_file_location('prior_mutation',ROOT/'research/verify-world-actor-mutation.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old);w,_,_=old.compile_case(old.fixtures()[0]);self.assertEqual(w[0],0x5045567a);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],0x574d3031)
 def test_carrier_and_immunity_regions_do_not_overlap(self):
  self.assertEqual(L['WORLD_ACTOR_RECIPIENT_WORDS'],168);self.assertEqual(L['WORLD_ACTOR_WIDE_IMMUNITY_BASE'],L['WORLD_ACTOR_RECIPIENT_BASE']+16+512*168);self.assertLessEqual(L['WORLD_ACTOR_WIDE_IMMUNITY_BASE']+128*256*2,L['WORLD_ACTOR_RECIPIENT_OUTPUT_WORDS'])
 def test_wire_limit_rejects_larger_unvalidated_output_before_build(self):
  import struct
  with patch('portable_backend.build',side_effect=AssertionError('No build')):
   with self.assertRaisesRegex(ValueError,'word strides'):execute(d.SOURCE,'portableEvents',struct.pack('<I',1),92336,524289)
 def test_zero_and_fractional_initial_counts_remain_literal(self):
  import struct
  for value in (0.,-0.,.5,-.5,9.):
   c=next(c for c in d.fixtures() if c['name']=='shared-init-value-'+repr(value));w,_,_=d.compile_case(c);self.assertEqual(w[L['DEFINITION_BASE']+32+6:L['DEFINITION_BASE']+32+8],list(struct.unpack('<II',struct.pack('<d',value))))
 def test_partial_removal_limit_is_literal(self):
  c=next(c for c in d.fixtures() if c['name']=='shared-partial-removal-enemies_top_atk:65');w,_,_=d.compile_case(c);self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+16:L['DAMAGE_DEFINITION_BASE']+18],[9,65])
 def test_old_abi_output_sizes_are_not_expanded(self):
  self.assertEqual(L['WORLD_ACTOR_RECIPIENT_ABI'],0x5045567b);self.assertEqual((L['OUTPUT_WORDS'],L['WORLD_ACTOR_FIELDS_OUTPUT_WORDS']),(159744,262144));self.assertEqual(L['WORLD_ACTOR_RECIPIENT_OUTPUT_WORDS'],524288)
if __name__=='__main__':unittest.main()
