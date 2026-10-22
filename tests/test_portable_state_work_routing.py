"""Route only authored prerequisite subsets; never convert them to GPU support."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_readiness_semantics import reference_readiness


class StateWorkRoutingTests(unittest.TestCase):
    def test_cover_camera_and_friendly_dependencies_are_explicit(self):
        rows=[dict(phase='effect',category='trigger',kind='buff',stat='focus_fire',target='all_allies',operator=dict(domain='condition',descriptor='focusing')),
              dict(phase='effect',category='trigger',kind='buff',stat='atk_caster_based_pct',target='allies_random:1',operator=dict(domain='condition',descriptor='no_broken_cover_ally')),
              dict(phase='effect',category='recipient',kind='instant',stat='cover_revive',target='allies_broken_cover_random:2'),
              dict(phase='effect',category='recipient',kind='buff',stat='atk_caster_based_pct',target='allies_random:1')]
        for i,row in enumerate(rows):
            with self.subTest(row=row):
                result=reference_readiness(row);self.assertEqual(result['lane'],'native_contract_extension' if i<2 else 'reference_review');self.assertFalse(result['gpu_supported']);self.assertFalse(result['gpu_admission_verified']);self.assertFalse(result['runtime_validation_performed'])
                if i<2:self.assertTrue(result['required_extensions'])
                else:
                    self.assertEqual(result['required_extensions'],[]);self.assertTrue(result['scoped_metal_validation_performed']);self.assertEqual(result['scoped_gpu_suite'],'ally-random-gpu')
        self.assertEqual(reference_readiness(rows[0])['required_extensions'],['focus_fire_live_marker_and_aim'])

    def test_unrecorded_operator_recipient_and_kind_are_not_promoted(self):
        for row in [dict(phase='effect',category='recipient',kind='damage',target='allies_random:1'),dict(phase='effect',category='recipient',kind='instant',target='allies_random_with_debuff:2'),dict(phase='effect',category='recipient',kind='buff',target='allies_random:0'),dict(phase='program',category='recipient',kind='buff',target='allies_random:1')]:
            self.assertEqual(reference_readiness(row)['lane'],'reference_review')


if __name__=='__main__':unittest.main()
