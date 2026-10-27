"""Device scope must preserve original cases, all words and shared providers."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('resident_device_test',ROOT/'research/verify-coordinate-resident-device-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ResidentDeviceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  rows,_=a.parent.prepare();cls.prefix=rows[:4];cls.total=len(rows)
 def test_complete_original_prefix_is_kept_without_native_or_gpu_choices(self):
  rows,_=a.prepare();self.assertEqual(tuple(r[0] for r in rows),a.CASES)
  for actual,old in zip(rows,self.prefix,strict=True):self.assertEqual(actual[1],old[1]);self.assertEqual(actual[2],old[2])
 def test_source_shape_missing_reordered_or_corrupt_prefix_is_rejected(self):
  source=list(self.prefix)+[('unused',[],None)]*(self.total-4)
  for fault in ('order','missing','domain','word'):
   rows=list(source)
   if fault=='order':rows[0],rows[1]=rows[1],rows[0]
   elif fault=='missing':rows.pop()
   elif fault=='domain':rows[0]=(rows[0][0],rows[0][1],None)
   else:
    name,words,domain=rows[0];words=list(words);words[-1]^=1;rows[0]=(name,words,domain)
   with self.subTest(fault=fault),patch.object(a.parent,'prepare',return_value=(rows,None)),self.assertRaises(ValueError):a.prepare()
 def test_native_provider_and_full_tail_comparison_are_the_existing_functions(self):
  for name in ('native_reference','compare','validate_rejection','native_comparison_adapter'):
   self.assertIs(getattr(a,name),getattr(a.parent,name))
  self.assertIs(a.NATIVE_COMPARISON_CONTEXT,a.parent.NATIVE_COMPARISON_CONTEXT)
 def test_registry_keeps_full_source_and_distinct_scoped_golden(self):
  import nikke_gpu as cli
  from portable_package_projection import SUPPORTED_SUITES
  self.assertIn('coordinate-resident-device',SUPPORTED_SUITES)
  full=cli.SUITES['coordinate-resident-arc'];short=cli.SUITES['coordinate-resident-device']
  self.assertEqual((short['inputs'],short['native']),(4,4));self.assertEqual(short['source'],full['source'])
  self.assertNotEqual(short['golden'],full['golden']);self.assertEqual(short['output_words'],full['output_words'])
  self.assertEqual((full['inputs'],full['native']),(106,63))

if __name__=='__main__':unittest.main()
