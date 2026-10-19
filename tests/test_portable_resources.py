"""Resource admission, native spend and boundary notification contracts."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import validate_effect
from portable_resource_oracle import observe
from resource_specs import consume_resource
from portable_specs import LIMITS as L
spec=importlib.util.spec_from_file_location('resource_verifier',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
CASES=json.loads((ROOT/'tests/fixtures/portable-resources.json').read_text())['cases']
class ResourceTests(unittest.TestCase):
    def effect(self):return copy.deepcopy(CASES[0]['effects'][0])
    def test_actual_spend_survives_cancellation(self):
        self.assertEqual(consume_resource(1e16,1,0),(1e16,1))
    def test_native_authored_contracts(self):
        for c in CASES:
            with self.subTest(name=c['name']):
                a=observe(c);v.contains(a['queries'],c['expected_queries'],c['name']);self.assertEqual(a['resource_queries'],c['expected_resource_queries'])
                if 'expected_resource_trace' in c:self.assertEqual(a['resource_trace'],c['expected_resource_trace'])
    def test_caps_and_keys_reject_invalid_inputs(self):
        for field,values in [('gauge_id',('', 'a:b',True,3)),('gauge_max',(-1,True,float('nan'),float('inf')))]:
            for value in values:
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):validate_effect({**self.effect(),field:value})
    def test_raw_cap_integer_cannot_silently_round(self):
        e={**self.effect(),'type':'buff','stat':'gauge_max_add','duration':-1}
        for value in (2**53+1,10**1000):
            with self.subTest(value=value),self.assertRaises(ValueError):validate_effect({**e,'fixed_value':value})
        validate_effect({**e,'fixed_value':10**16})
    def test_marker_is_state_only(self):
        e={**self.effect(),'type':'buff','stat':'gauge_charge_enabled','duration':-1};e.pop('fixed_value')
        validate_effect(e)
        for field,value in [('fixed_value',1),('max_stack',2),('target','all_allies')]:
            with self.subTest(field=field),self.assertRaises(ValueError):validate_effect({**e,field:value})
    def test_condition_modulus_wire_bounds(self):
        e=copy.deepcopy(next(c for c in CASES if 'modulo-beyond' in c['name'])['effects'][1])
        for expression in ('gauge_mod:large:0:0','gauge_mod:large:2147483648:0','gauge_mod:large:3:2147483648'):
            c=copy.deepcopy(CASES[0]);e['trigger']['condition']=[expression];c['effects'].append(copy.deepcopy(e));c['owners'].append(0)
            with self.subTest(expression=expression),self.assertRaises(ValueError):v.compile_case(c)
    def test_resource_queries_do_not_supply_cpu_quantities(self):
        c=next(c for c in CASES if c['name']=='resource-same-instant-name-different-keys');words,meta=v.compile_case(c)
        self.assertEqual(words[L['RESOURCE_META_BASE']],2)
        self.assertEqual(len(words),L['INPUT_WORDS'])
        self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS']),(77824,94208))
if __name__=='__main__':unittest.main()
