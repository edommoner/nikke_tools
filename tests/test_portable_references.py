"""Authoring and precedence contracts for GPU-owned referenced hit counts."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_reference_specs import hit_reference
from portable_specs import LIMITS as L
sp=importlib.util.spec_from_file_location('reference_verifier',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
CS=json.loads((ROOT/'tests/fixtures/portable-hit-references.json').read_text())['cases']
class ReferenceInputTests(unittest.TestCase):
    def test_native_hit_precedence_has_distinct_modes(self):
        self.assertEqual(hit_reference(dict(type='damage',stat='damage:3',hit_count_gauge_ref='MP')),(2,'MP'))
        self.assertEqual(hit_reference(dict(type='damage',stat='damage:3',scaling='stack_count',scaling_ref='MP')),(0,None))
        self.assertEqual(hit_reference(dict(type='damage',stat='damage',scaling='stack_count',scaling_ref='MP')),(1,'MP'))
        self.assertEqual(hit_reference(dict(type='damage',stat='dot_damage',scaling='stack_count')),(0,None))
    def test_invalid_resource_names_and_types_reject(self):
        for value in ('',None,True,3,'bad:key'):
            e=dict(type='damage',stat='damage',hit_count_gauge_ref=value)
            # Missing/None isn't an authored reference; the legacy admission
            # still rejects an explicitly authored non-string payload.
            if value is None:
                with self.assertRaises(ValueError):v.compile_case({**CS[0],'effects':[e],'owners':[0]})
            else:
                with self.subTest(value=value),self.assertRaises(ValueError):hit_reference(e)
        with self.assertRaises(ValueError):hit_reference(dict(type='damage',stat=None))
    def test_wire_contains_identity_without_live_quantity(self):
        c=CS[0];words,meta=v.compile_case(c);at=L['REFERENCE_DEFINITION_BASE']+2*4
        self.assertEqual(words[at],1);self.assertEqual(words[at+3],0)
        self.assertEqual(words[L['RESOURCE_NAME_BASE']+words[at+1]-1],words[at+2])
        self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS']),(77824,94208))
    def test_external_dot_uses_separate_coefficient_reference(self):
        c=copy.deepcopy(CS[0]);c['effects'][2].update(stat='dot_damage',tick_interval=.25,duration=1,scaling='stack_count',scaling_ref='fuel')
        words,_=v.compile_case(c);at=L['REFERENCE_DEFINITION_BASE']+2*4
        self.assertEqual(words[at]&3,0);self.assertEqual(words[at]>>2,3)
        self.assertEqual(words[L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+28]&4,4)
        self.assertLessEqual(L['REFERENCE_CAPTURE_BASE']+L['CARRIERS']*3,L['OUTPUT_WORDS'])
    def test_existing_source_and_query_only_resource_names_fit(self):
        cs=json.loads((ROOT/'tests/fixtures/portable-resources.json').read_text())['cases']
        c=next(c for c in cs if c['name']=='resource-present-zero-is-distinct-from-absent')
        words,meta=v.compile_case(c);self.assertEqual(len(meta['resource_names']),2)
        self.assertTrue(all(words[L['RESOURCE_NAME_BASE']+i]<256 for i in range(2)))
if __name__=='__main__':unittest.main()
