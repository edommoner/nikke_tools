import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import ABI,LIMITS as L
from portable_runtime_layout import runtime_initializer
class ModeEntryContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  spec=importlib.util.spec_from_file_location('mode_entry_test_core',ROOT/'scripts/verify-portable-combat.py');cls.core=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.core)
  cls.entries=json.loads((ROOT/'tests/fixtures/portable-mode-entry.json').read_text())['cases'];cls.pending=json.loads((ROOT/'tests/fixtures/portable-pending-reference.json').read_text())['cases']
 def test_presence_distinguishes_explicit_zero_from_absence(self):
  explicit=self.entries[0];absent=next(c for c in self.entries if '-absent-' in c['name']);a,ma=self.core.compile_case(explicit);b,mb=self.core.compile_case(absent);at=L['MODE_BASE']+2*L['MODE_WORDS']+28
  self.assertEqual(a[at:at+4],[0,0,1,0]);self.assertEqual(b[at:at+4],[0]*4);self.assertTrue(ma['mode_entry_enabled']);self.assertFalse(mb['mode_entry_enabled'])
 def test_authored_metadata_bounds_reject_before_packing(self):
  for value in (-1,181,True,float('nan'),float('inf')):
   c=copy.deepcopy(self.entries[0]);c['mode_entry_context']['delays']['Mode A']=value
   with self.subTest(value=value),self.assertRaises(ValueError):self.core.compile_case(c)
 def test_native_wait_and_physical_clock_are_independent_of_post_reload(self):
  from portable_mode_entry_oracle import observe
  c=next(c for c in self.entries if c['name']=='mode-entry-0-auto-auto-0.39-short');n=observe(c)
  self.assertEqual(n['mode_entry_wait_until'],[.39,-1,-1,-1,-1]);self.assertEqual(n['weapons'][0]['post_reload_until'],-1)
  self.assertEqual(n['queries'][-1]['damage'],[0]*5)
 def test_native_pending_multiplies_coefficient_before_one_rounding(self):
  from portable_pending_reference_oracle import observe
  from portable_pending_reference_context import data_context
  c=next(c for c in self.pending if c['name']=='pending-reference-0-three-1.1')
  with data_context(c):n=observe(c)
  self.core.contains(n['queries'],c['expected_queries'],c['name']);self.assertEqual(len(n['packets']),1);self.assertEqual(n['packets'][0]['delivered_amount'],50)
 def test_initializer_tail_and_malformed_admission_contract(self):
  from portable_mode_entry_validation import rejection_programs
  self.assertEqual(ABI,0x50455672);self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS']),(86016,159744));self.assertLessEqual(L['MODE_ENTRY_STATE_BASE']+10,L['OUTPUT_WORDS'])
  generated=runtime_initializer();self.assertIn('s.modeEntryUntil[index] = 0;',generated);self.assertEqual(generated,(ROOT/'gpu/runtime_init.slang').read_text())
  before=copy.deepcopy(self.entries);bad,rows=rejection_programs(self.entries,self.core.compile_case);self.assertEqual(len(bad),11);self.assertEqual([r['status'] for r in rows],[64]*11);self.assertEqual(self.entries,before)
if __name__=='__main__':unittest.main()
