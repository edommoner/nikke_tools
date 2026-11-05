"""Subtract signed count adjustments before the canonical minimum-one clamp."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker,portable_backend
from portable_nonfull_charge_specs import compiler_effect,parse
from portable_partial_charge_reduction_cases import fixtures
from portable_nonfull_charge_contracts import verify
from world_nonfull_charge_native import observe
from world_projectile_native import observe as plain
from portable_specs import LIMITS as L


class SignedCountTests(unittest.TestCase):
 def test_all7_canonical_contracts_preserve_battle_and_trace(self):
  cases=fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),7)
  for c in cases:
   with self.subTest(case=c['name']),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
    n,t=observe(c);verify(c,n);n.pop('nonfull_charge');expected,trace=plain(c);self.assertEqual(n,expected);self.assertEqual(t,trace)
  self.assertEqual(cases,before)

 def test_legacy_intermediate_does_not_erase_the_restored_signed_wire_base(self):
  s=importlib.util.spec_from_file_location('signed_wire',ROOT/'research/verify-world-partial-charge-reduction-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,data=m.prepare();self.assertEqual(len(rows),11)
  for name,w,d in rows[:7]:
   c=d[0];raw=parse(c['effects'][1]['trigger']['timing'][0])[0];at=L['EVENT_BASE']+L['EVENT_WORDS'];value=struct.unpack('<d',struct.pack('<II',*w[at+1:at+3]))[0]
   self.assertEqual(value,max(1,raw));self.assertEqual(w[at+5],int(raw<=0));self.assertEqual(w[at+4],raw&0xffffffff if raw<=0 else 0xffffffff)
   effect=c['effects'][1];before=copy.deepcopy(effect);lowered=compiler_effect(effect);self.assertEqual(effect,before)
   if raw<=0 or abs(raw)>100000000:self.assertEqual(lowered['trigger']['timing'],['non_full_charge_fire_count:1'])
  self.assertTrue(all(w!=rows[0][1] for _,w,_ in rows[7:]))

 def test_out_of_range_bases_fail_before_legacy_or_gpu(self):
  for raw in ('-2147483649','2147483648','1.5','+1'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):parse('non_full_charge_fire_count:'+raw)


if __name__=='__main__':unittest.main()
