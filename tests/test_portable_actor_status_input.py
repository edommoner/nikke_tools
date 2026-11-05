"""Typed status wiring carries definitions,not CPU immunity or cleanse results."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('status_input',ROOT/'research/verify-world-actor-status.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
from calculator.boss_pattern import BossScript
from portable_specs import LIMITS as L
class StatusInput(unittest.TestCase):
 def test_pack128_without_cpu_tick_or_recipient_resolution(self):
  c=next(c for c in d.fixtures() if c['name']=='128-count-immunity-1.5');before=copy.deepcopy(c)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU clock')),patch.object(BossScript,'resolve_enemies',side_effect=AssertionError('No CPU status scopes')):w,m,b=d.compile_case(c)
  self.assertEqual(c,before);self.assertEqual(len(b),128);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],d.MAGIC);self.assertEqual(w[0],0x5045567c)
 def test_capacity_fraction_is_not_preconverted_to_integer(self):
  import struct
  c=next(c for c in d.fixtures() if c['name']=='128-count-immunity-1.5');w,_,_=d.compile_case(c);self.assertEqual(w[L['DEFINITION_BASE']+6:L['DEFINITION_BASE']+8],list(struct.unpack('<II',struct.pack('<d',1.5))))
 def test_count_bank_has128_disjoint_namespaces(self):
  base=L['WORLD_ACTOR_WIDE_IMMUNITY_BASE'];self.assertLess(base+127*512+255*2+1,L['WORLD_ACTOR_RECIPIENT_OUTPUT_WORDS']);self.assertEqual((base+127*512)-(base+126*512),512)
 def test_cleanse_all_keeps_literal128_limit(self):
  c=next(c for c in d.fixtures() if c['name']=='typed-cleanse-limit-1.0');w,_,_=d.compile_case(c);self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+16:L['DAMAGE_DEFINITION_BASE']+18],[2,128])
 def test_ranked_cleanse_keeps65_limit(self):
  c=next(c for c in d.fixtures() if c['name']=='typed-cleanse-scope-enemies_top_atk:65');w,_,_=d.compile_case(c);self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+8:L['DAMAGE_DEFINITION_BASE']+10],[9,65])
 def test_old_shared_entry_policy_and_abi_are_retained(self):
  c=d.recipient.fixtures()[0];w,_,_=d.recipient.compile_case(c);self.assertEqual(w[0],0x5045567b);self.assertEqual(w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],0x57523031)
 def test_nonfinite_capacity_negative_input_targets_count_definition(self):
  rows,programs,bad=d.prepare();w=dict(bad)['count-nonfinite-capacity'];self.assertEqual((w[L['DEFINITION_BASE']+28]>>4)&3,3);self.assertEqual(w[L['DEFINITION_BASE']+7],0x7ff00000)
 def test_hit_only_max_rank_is_preserved_as_explicit_negative(self):
  _,_,bad=d.prepare();w=dict(bad)['pure-hit-hp-max-rank-unresolved-native-contract'];self.assertEqual(w[L['WORLD_ACTOR_POOL_DEF_BASE']+12],3)
if __name__=='__main__':unittest.main()
