"""Packing fixture tables must not execute discarded native battles."""
import array,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def load():
 s=importlib.util.spec_from_file_location('overlay_pure_cases',ROOT/'research/verify-world-overlay-body.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class PurityTests(unittest.TestCase):
 def test_authored_cases_and_packed_bytes_keep_prechange_fingerprints_without_oracle(self):
  m=load();expected=json.loads((ROOT/'tests/fixtures/portable-overlay-authored-cases-before.json').read_text())['entries'];actual=[]
  with patch.object(m.n,'observe',side_effect=AssertionError('Oracle forbidden during case construction')),patch.object(m.n,'full_simulations',side_effect=AssertionError('Full battles forbidden')):
   cases=m.cases()
   for c in cases:
    w,meta=m.compile_case(c);packed=array.array('I',w)
    if sys.byteorder!='little':packed.byteswap()
    actual.append(dict(name=c['name'],case_sha256=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),input_sha256=hashlib.sha256(packed.tobytes()).hexdigest()))
  self.assertEqual(actual,expected)
 def test_authored_tables_are_fresh_and_native_witnesses_are_still_executed_explicitly(self):
  m=load();first=m.n.simulation_cases();first[0]['patterns'][0]['id']='mutated'
  self.assertEqual(m.n.simulation_cases()[0]['patterns'][0]['id'],'base')
  original=m.n.observe
  with patch.object(m.n,'observe',wraps=original) as observed:
   rows=m.n.full_simulations()
  self.assertEqual(observed.call_count,7);self.assertTrue(all(r['passed'] for r in rows))
if __name__=='__main__':unittest.main()
