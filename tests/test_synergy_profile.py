import json
from pathlib import Path
import unittest

from app.synergy_profile import TIER_B_TRAITS, build_profiles


def effect(target='self', stat='atk_pct', **extra):
    return dict(target=target, stat=stat, source='skill', name='base', type='buff', **extra)


class SynergyProfileTests(unittest.TestCase):
    def test_selectors_and_tiers(self):
        cases = [
            ('allies_code:전격', 'element', 'A', {'value': '전격'}),
            ('allies_code_excl_self:전격', 'element', 'A', {'excl_self': True}),
            ('allies_weapon:SG', 'weapon', 'A', {'value': 'SG'}),
            ('allies_weapon_excl_self:SG', 'weapon', 'A', {'excl_self': True}),
            ('allies_burst_casted_weapon:MG', 'weapon', 'A', {'value': 'MG'}),
            ('allies_weapon_top_atk:SG:2', 'weapon', 'A', {'value': 'SG'}),
            ('allies_class:방어형:2', 'class', 'A', {'value': '방어형'}),
            ('allies_code_weapon:전격:AR', 'element_weapon', 'A', {'element': '전격', 'weapon': 'AR'}),
            ('allies_code_weapon_leftmost:전격:AR:1', 'element_weapon', 'A', {'weapon': 'AR'}),
            ('allies_squad', 'squad', 'A', {}),
            ('allies_burst_casted_burst3', 'burst', 'A', {'value': '3'}),
            ('allies_lowest_atk_burst3:1', 'burst', 'A', {'value': '3'}),
            ('allies_burst3_persona_excl_self', 'squad_burst', 'A', {'excl_self': True}),
            ('receiver', 'name', 'A', {'value': 'receiver'}),
        ]
        for target, kind, tier, fields in cases:
            with self.subTest(target=target):
                p = build_profiles({'owner': [effect(target)], 'receiver': []}, {})['owner']['provides'][0]
                self.assertEqual((p['tier'], p['selector']['kind']), (tier, kind))
                for key, value in fields.items():
                    self.assertEqual(p['selector'][key], value)
        for target in ['all_allies', 'all_allies_excl_self', 'all_allies_burst_casted', 'all_allies_burst_not_casted']:
            for stat, trait in TIER_B_TRAITS.items():
                p = build_profiles({'x': [effect(target, stat)]}, {})['x']['provides'][0]
                self.assertEqual(p['tier'], 'B')
                self.assertEqual(p['selector'], dict(kind='trait', value=trait, excl_self='excl_self' in target))
            self.assertEqual(build_profiles({'x': [effect(target)]}, {})['x']['provides'][0]['tier'], 'C')

    def test_skips_dynamic_and_compound_targets(self):
        ignored = ['self', 'all_enemies', 'target', 'same_target:x', 'boss', 'all_projectiles', 'target_body', 'self_cover']
        effects = [effect(t) for t in ignored] + [effect('all_allies', polarity='harmful'),
                   effect(['self', 'allies_top_atk:2']), effect('allies_random_excl_self:1')]
        p = build_profiles({'x': effects}, {})['x']
        self.assertEqual([e['selector'] for e in p['provides']], [
            {'kind': 'dynamic', 'rule': 'allies_top_atk'},
            {'kind': 'dynamic', 'rule': 'allies_random_excl_self', 'excl_self': True}])
        self.assertTrue(all(e['tier'] == 'C' for e in p['provides']))

    def test_deduplication_and_conditions(self):
        trigger = {'condition': ['squad_ally_exists', 'has_burst1_ally', 'no_burst1_ally',
                                'has_defender_ally', 'no_defender_ally', 'prob:20'],
                   'timing': ['squad_burst_cast:2']}
        favorite = effect('allies_weapon:SG', favorite=1, trigger=trigger)
        favorite['name'] = 'favorite'
        base = effect('allies_weapon:SG', trigger=trigger)
        base['source'] = 'base skill'
        for effects in [[favorite, base, favorite], [base, favorite]]:
            p = build_profiles({'x': effects}, {})['x']
            self.assertEqual(len(p['provides']), 1)
            self.assertEqual(len(p['conditions']), 6)
            for entry in p['provides'] + p['conditions']:
                self.assertFalse(entry['favorite'])
                self.assertEqual((entry['source'], entry['name']), ('base skill', 'base'))
        p = build_profiles({'x': [favorite, favorite]}, {})['x']
        self.assertTrue(all(e['favorite'] for e in p['provides'] + p['conditions']))
        self.assertIn(dict(kind='has_burst', value='2', negate=False, source='skill', name='favorite', favorite=True), p['conditions'])
        self.assertFalse(build_profiles({'x': [effect('self', trigger={'timing': ['squad_burst_cast:2']})]}, {})['x']['conditions'])

    def test_traits(self):
        skills = {'x': [effect(stat=s) for s in ['pierce_enabled', 'armor_break_enabled',
                  'projectile_explosion_dmg_pct', 'split_dmg_pct', 'dot_dmg_pct']],
                  'rl': [], 'mg': [], 'sg': [],
                  'damage': [dict(type='damage', stat='split_damage', tick_interval=1)]}
        p = build_profiles(skills, {'x': {'is_charge': True}, 'rl': {'weapon_type': 'RL'},
                                  'mg': {'weapon_type': 'MG'}, 'sg': {'weapon_type': 'SG'}})
        self.assertEqual(p['x']['traits'], ['armor_break', 'charge', 'dot', 'explosion', 'pierce', 'split'])
        for name, traits in [('rl', ['explosion']), ('mg', ['mg']), ('sg', ['sg']), ('damage', ['dot', 'split'])]:
            self.assertEqual(p[name]['traits'], traits)

    def test_real_upstream(self):
        data = Path(__file__).resolve().parents[1] / 'research/upstream/nikke-calc-master/data'
        skills = json.loads((data / 'parsed_skills.json').read_text())
        meta = json.loads((data / 'parsed_nikke.json').read_text())
        profiles = build_profiles(skills, meta)
        self.assertEqual(set(profiles), set(skills))
        for character, kind, value in [('토브', 'weapon', 'SG'), ('아르카나', 'element', '전격'), ('아르카나', 'name', '이사벨')]:
            self.assertTrue(any(e['tier'] == 'A' and e['selector']['kind'] == kind and e['selector']['value'] == value for e in profiles[character]['provides']))
        self.assertTrue(any(e['tier'] == 'C' and e['stat'] == 'atk_dmg_pct' and e['selector']['kind'] == 'all' for e in profiles['헬름']['provides']))
        traits = {t for p in profiles.values() for t in p['traits']}
        self.assertTrue(set(TIER_B_TRAITS.values()) <= traits)


if __name__ == '__main__':
    unittest.main()
