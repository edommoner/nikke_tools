import importlib.util
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('counts_verifier',ROOT/'scripts/verify-counts-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import UnsupportedDetail,REDUCER_MASK

class TriggerCountCompilerTests(unittest.TestCase):
 def test_authored_positive_counts_agree_with_independent_cpu(self):
  stats={n:{'atk':100000,'def':20000,'hp':1000000} for n in v.NAMES}
  for name,p,script,expected in v.primitives():
   with self.subTest(name=name):
    cpu,_=v.oracle.oracle(p,script,[31784,0,0,0,0,0],stats)
    self.assertEqual(cpu[0][37],expected)

 def test_raw_timing_group_identity_and_partial_counter_descriptor(self):
  cases={name:p for name,p,_,_ in v.primitives()}
  shared=cases['same-raw-timing-group']['effects'][-1]
  different=cases['raw-timing-spelling-is-distinct']['effects'][-1]
  self.assertEqual(int(shared[REDUCER_MASK])&1,1)
  self.assertEqual(int(different[REDUCER_MASK])&1,0)
  partial=cases['reduced-non_full_charge_fire_count']['effects'][-1]
  self.assertEqual(partial[145:148],[40,5,1])
  self.assertEqual(partial[151],1)

 def test_invalid_reduction_values_and_instant_variant_fail_closed(self):
  for fields in ({'fixed_value':float('nan')},{'fixed_value':1e10},{'target_effect':[]},{'type':'instant'}):
   eff=v.E('invalid reducer','buff','trigger_count_reduce',2,target_effect='counter result')|fields
   with self.subTest(fields=fields),self.assertRaises(UnsupportedDetail):
    v.oracle.program(v.oracle.characters(v.NAMES),[(eff,v.NAMES[0])])

class TriggerCountGPUTests(unittest.TestCase):
 def test_independent_counters_and_complete_squads(self):
  device=v.Cuda()
  try:cases=v.verify(device,'native')
  finally:device.close()
  self.assertTrue(cases)
  self.assertTrue(all(c['passed'] for c in cases),[c for c in cases if not c['passed']])

if __name__=='__main__':unittest.main()
