"""Confirmed partial-charge consumer routing cannot promote GPU admission."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_readiness_semantics import reference_readiness


class NonFullRoutingTests(unittest.TestCase):
    def test_all_four_catalog_definition_shapes_have_confirmed_native_prerequisites(self):
        for kind,stat,target in [('buff','atk_caster_based_pct','all_allies'),('buff','def_caster_based_pct','allies_without_buff:x'),('instant','debuff_cleanse','allies_without_buff:x'),('instant','remove_named_buff','all_allies')]:
            r=reference_readiness(dict(phase='effect',category='trigger',kind=kind,stat=stat,target=target,operator=dict(domain='timing',descriptor='non_full_charge_fire_count:3')))
            self.assertEqual(r['lane'],'native_contract_extension');self.assertEqual(r['reference_suites'],['nonfull-charge','nonfull-charge-reduction','partial-query']);self.assertEqual(r['recorded_cases'],47)
            for key in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertIs(r[key],False)
            self.assertIn('partial_charge_weapon_state_and_tap_controls',r['implemented_extensions'])
            self.assertEqual(r['scoped_metal_cases'],65);self.assertTrue(r['scoped_metal_validation_performed'])
            self.assertIn('tap_numeric_query_timing_and_rng',r['implemented_extensions'])
            self.assertIn('broader_numeric_stats_and_control_interleavings',r['required_extensions'])

    def test_other_domains_and_malformed_descriptors_do_not_inherit_evidence(self):
        for domain,text in [('condition','non_full_charge_fire_count:3'),('timing','full_charge_fire_count:3'),('timing','non_full_charge_fire_count:'),('timing','non_full_charge_fire_count:0'),('timing','non_full_charge_fire_count:3:4')]:
            r=reference_readiness(dict(phase='effect',category='trigger',kind='instant',operator=dict(domain=domain,descriptor=text)))
            self.assertEqual(r['lane'],'reference_review');self.assertNotIn('reference_suites',r)


if __name__=='__main__':unittest.main()
