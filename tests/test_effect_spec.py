import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import effect_spec as s

class EffectSpecificationTests(unittest.TestCase):
    def test_every_raw_effect_has_a_semantic_family(self):
        raw=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'))
        missing=[(name,i,e.get('stat')) for name,effects in raw.items() if isinstance(effects,list)
                 for i,e in enumerate(effects) if s.describe_effect(e)['family']=='unclassified']
        self.assertEqual(missing,[])
    def test_classification_does_not_claim_support_or_game_verification(self):
        shield=s.describe_effect({'type':'buff','stat':'shield_dmg_pct'})
        self.assertFalse(shield['registered_numeric_stat'])
        self.assertTrue(shield['compiler_acceptance_required'])
        self.assertEqual(s.describe_effect({'stat':'heal_split'})['evidence'],'explicit_reference_model')
        self.assertEqual(s.describe_effect({'stat':'new_unknown'})['family'],'unclassified')
    def test_existing_abi_and_distinct_buffer_rules_are_preserved(self):
        self.assertEqual(s.EXTRA_STAT['heal_overcharge_store'],74)
        self.assertEqual(s.EXTRA_STAT['heal_overcharge_store_atk_pct'],76)
        self.assertEqual(s.EXTRA_STAT['accumulate_max_scale_pct'],77)
        self.assertLess(s.RECOVERY_ORDER.index('sharing_allocation'),s.RECOVERY_ORDER.index('body_hp_clamp'))
        self.assertLess(s.COMPAT_LAYERS.index('target_counter_runtime'),s.COMPAT_LAYERS.index('periodic_source_runtime'))
        self.assertLess(s.COMPAT_LAYERS.index('base_copy_runtime'),s.COMPAT_LAYERS.index('damage_query_runtime'))
        self.assertLess(s.COMPAT_LAYERS.index('heal_sharing_compat'),s.COMPAT_LAYERS.index('damage_query_runtime'))
        self.assertLess(s.COMPAT_LAYERS.index('heal_charge_compat'),s.COMPAT_LAYERS.index('damage_accum_runtime'))

if __name__=='__main__':unittest.main()
