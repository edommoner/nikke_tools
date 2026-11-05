"""Stack scope/value packing remains static and independent of CPU battle state."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('typed_stack_input',ROOT/'research/verify-world-actor-stacks.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
from calculator.boss_pattern import BossScript
from portable_specs import LIMITS as L
class StackInput(unittest.TestCase):
 def test_pack_without_cpu_clock_or_target_resolution(self):
  c=next(c for c in d.fixtures() if c['name']=='shared-once-debuff_stack_add-seed');before=copy.deepcopy(c)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU stack state')),patch.object(BossScript,'resolve_enemies',side_effect=AssertionError('No CPU snapshot')):w,m,b=d.compile_case(c)
  self.assertEqual(c,before);self.assertEqual(len(b),128);self.assertEqual(w[0],0x5045567d);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],d.MAGIC)
 def test_all_scope_count_is128(self):
  c=next(c for c in d.fixtures() if c['name']=='independent-debuff_stack_add-all_enemies');w,_,_=d.compile_case(c);self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+8:L['DAMAGE_DEFINITION_BASE']+10],[2,128])
 def test_partial_shared_scope_is65(self):
  c=next(c for c in d.fixtures() if c['name']=='shared-once-debuff_stack_add-seed');w,_,_=d.compile_case(c);self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+16:L['DAMAGE_DEFINITION_BASE']+18],[9,65])
 def test_fractional_delta_remains_binary64_literal(self):
  import struct
  c=next(c for c in d.fixtures() if c['name']=='stack-delta-debuff_stack_add-3.9');w,_,_=d.compile_case(c);self.assertEqual(w[L['DEFINITION_BASE']+32+6:L['DEFINITION_BASE']+32+8],list(struct.unpack('<II',struct.pack('<d',3.9))))
 def test_zero_delta_keeps_sign_for_shared_integer_policy(self):
  import struct
  for v in (0.,-0.):
   c=next(c for c in d.fixtures() if c['name']=='stack-delta-debuff_stack_remove-'+repr(v));w,_,_=d.compile_case(c);self.assertEqual(w[L['DEFINITION_BASE']+32+6:L['DEFINITION_BASE']+32+8],list(struct.unpack('<II',struct.pack('<d',v))))
 def test_old_status_policy_retained(self):
  w,_,_=d.status.compile_case(d.status.fixtures()[0]);self.assertEqual(w[0],0x5045567c);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],0x57493031)
 def test_shared_capture_stride_unchanged(self):
  self.assertEqual(L['WORLD_ACTOR_RECIPIENT_WORDS'],168);self.assertEqual(L['WORLD_ACTOR_RECIPIENT_OUTPUT_WORDS'],524288);self.assertEqual(L['WORLD_ACTOR_STATE_INPUT_WORDS'],92336)
 def test_bad_scope_words_are_literal_negatives(self):
  _,_,bad=d.prepare();w=dict(bad)['stack-scope-count-overflow'];self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+9],257)
if __name__=='__main__':unittest.main()
