"""Native context prerequisites never imply portable admission or GPU coverage."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_readiness_semantics import reference_readiness


class NotCoreRoutingTests(unittest.TestCase):
    def test_known_gauge_definition_has_native_prerequisites_without_gpu_promotion(self):
        issue=dict(phase='effect',category='trigger',kind='instant',stat='gauge_charge',target='self',operator=dict(domain='condition',descriptor='not_core'))
        r=reference_readiness(issue);self.assertEqual(r['lane'],'native_contract_extension');self.assertEqual(r['reference_suites'],['not-core']);self.assertEqual(r['recorded_cases'],27)
        self.assertEqual((r['real_original_definitions'],r['real_durations']),(79,[3,30]))
        self.assertEqual(r['real_instant_handler_calls'],[3,34])
        for k in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertIs(r[k],False)
        self.assertEqual(r['scoped_metal_validation']['native_cases'],27)
        self.assertEqual(r['scoped_metal_validation']['rejected_cases'],5)
        self.assertTrue(r['scoped_metal_validation']['independently_audited'])
        self.assertIn('broader_mixed_passive_numeric_context_consumers',r['required_extensions'])

    def test_other_domains_and_malformed_conditions_do_not_inherit_context_evidence(self):
        for domain,text in [('timing','not_core'),('condition','not_core:0'),('condition','core_hit'),('condition','not_core '),('condition','not_core_hit')]:
            r=reference_readiness(dict(phase='effect',category='trigger',operator=dict(domain=domain,descriptor=text)))
            self.assertEqual(r['lane'],'reference_review');self.assertNotIn('reference_suites',r)

    def test_host_not_core_requires_a_physical_world(self):
        from portable_trigger_specs import validate_input
        effect=dict(trigger=dict(timing=['hit_count'],condition=['not_core']))
        with self.assertRaises(ValueError):validate_input(effect,world_frame=False)
        validate_input(effect,world_frame=True)



if __name__=='__main__':unittest.main()
