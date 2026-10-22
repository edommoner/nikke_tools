"""Route only authored prerequisite subsets; never convert them to GPU support."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_readiness_semantics import reference_readiness


class StateWorkRoutingTests(unittest.TestCase):
    def test_cover_camera_and_friendly_dependencies_are_explicit(self):
        rows=[dict(phase='effect',category='trigger',kind='buff',stat='focus_fire',target='all_allies',operator=dict(domain='condition',descriptor='focusing')),
              dict(phase='effect',category='trigger',kind='buff',stat='atk_pct',target='allies_random:1',operator=dict(domain='condition',descriptor='no_broken_cover_ally')),
              dict(phase='effect',category='recipient',kind='instant',stat='cover_revive',target='allies_broken_cover_random:2'),
              dict(phase='effect',category='recipient',kind='buff',stat='def_pct',target='allies_random:1')]
        for i,row in enumerate(rows):
            with self.subTest(row=row):
                result=reference_readiness(row);self.assertEqual(result['lane'],'reference_review');self.assertFalse(result['gpu_supported']);self.assertFalse(result['gpu_admission_verified']);self.assertFalse(result['runtime_validation_performed'])
                self.assertEqual(result['required_extensions'],[]);self.assertTrue(result['scoped_metal_validation_performed']);self.assertEqual(result['scoped_gpu_suite'],'state-focus' if i<2 else 'ally-random-gpu')
        pending=dict(rows[0],stat='lifesteal_pct');result=reference_readiness(pending)
        self.assertEqual(result['lane'],'native_contract_extension');self.assertEqual(result['required_extensions'],['numeric_query_reader_cache_contract'])

    def test_physical_interrupt_is_a_typed_adapter_extension(self):
        result=reference_readiness(dict(phase='program',category='control',fields=['focus_aim_physical_interrupt']))
        self.assertEqual(result['lane'],'native_contract_extension');self.assertEqual(result['contract_coverage'],'reproduced_adapter_rejection');self.assertIn('typed_interrupt_actor_bridge',result['required_extensions']);self.assertFalse(result['gpu_supported'])

    def test_late_attack_random_is_not_covered_by_generic_recipient_proof(self):
        for stat in ('atk_caster_based_pct','atk_from_hp_pct'):
            for category in ('recipient','trigger','effect'):
                result=reference_readiness(dict(phase='effect',category=category,kind='buff',stat=stat,target='allies_random:1',operator=dict(domain='condition',descriptor='no_broken_cover_ally')))
                self.assertEqual(result['lane'],'native_contract_extension')
                self.assertEqual(result['reference_suites'],['late-attack-random'])
                self.assertIn('dictionary_query_cache_boundaries',result['implemented_extensions'])
                self.assertIn('current_source_cuda_validation',result['required_extensions'])
                self.assertEqual((result['recorded_cases'],result['scoped_metal_cases']),(11,17))
                self.assertFalse(result['gpu_supported']);self.assertFalse(result['runtime_validation_performed'])

    def test_unrecorded_operator_recipient_and_kind_are_not_promoted(self):
        for row in [dict(phase='effect',category='recipient',kind='damage',target='allies_random:1'),dict(phase='effect',category='recipient',kind='instant',target='allies_random_with_debuff:2'),dict(phase='effect',category='recipient',kind='buff',target='allies_random:0'),dict(phase='program',category='recipient',kind='buff',target='allies_random:1')]:
            self.assertEqual(reference_readiness(row)['lane'],'reference_review')


if __name__=='__main__':unittest.main()
