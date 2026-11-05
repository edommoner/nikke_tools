from detail_gpu import compile_effects,UnsupportedDetail,TD,TS,DETAIL_ABI
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('event_tests',ROOT/'scripts/verify-events-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class EventDescriptorCompilerTests(unittest.TestCase):
 def compile(self,timings):
  e=v.E('test','buff','atk_pct',1);e['trigger']['timing']=timings
  return compile_effects(v.oracle.characters(v.NAMES),[(e,v.NAMES[0])])
 def test_multiple_parameters_and_duplicate_index_entries_are_preserved(self):
  q=self.compile(['received_hit_count:2','received_hit:3','received_hit:3'])['effects'][0]
  self.assertEqual(q[144],3);self.assertEqual([q[TD+i*TS+1] for i in range(3)],[2,3,3]);self.assertTrue(all(q[TD+i*TS]==32 for i in range(3)))
 def test_descriptor_bound_and_multiple_every_entries(self):
  with self.assertRaises(UnsupportedDetail):self.compile([f'on_attack_count:{i}' for i in range(1,10)])
  q=self.compile(['every:0.5s','every:1s','every:1s'])['effects'][0]
  self.assertEqual([q[TD+i*TS+1] for i in range(3)],[.5,1,1])
if __name__=='__main__':unittest.main()
