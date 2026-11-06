import json
from pathlib import Path
import unittest

from app.synergy_profile import TIER_B_TRAITS, build_profiles, build_damage_groups


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

    def test_dynamic_targets_with_tier_b_stats_keep_the_trait(self):
        p = build_profiles({'x': [effect('allies_below_def', stat='projectile_explosion_dmg_pct'),
                                  effect('allies_top_atk_excl:1', stat='charge_dmg_pct')]}, {})['x']['provides']
        self.assertEqual([(e['tier'], e['selector']) for e in p], [
            ('B', {'kind': 'trait', 'value': 'explosion', 'rule': 'allies_below_def'}),
            ('B', {'kind': 'trait', 'value': 'charge', 'rule': 'allies_top_atk_excl'})])

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



class DamageGroupTests(unittest.TestCase):
    def test_mapping_and_scopes(self):
        cases = [('normal_atk_dmg_pct', '1'), ('atk_pct', '2'),
                 ('atk_caster_based_pct', '2'), ('atk_from_hp_pct', '2'),
                 ('def_ignore_pct', '2'), ('crit_rate', '3'), ('crit_dmg', '3'),
                 ('normal_atk_crit_rate', '3'), ('core_dmg_pct', '3'),
                 ('charge_dmg_pct', '4'), ('charge_dmg_mag_pct', '4'),
                 ('atk_dmg_pct', '5'), ('burst_dmg_pct', '5'), ('burst_dmg_aoe_pct', '5'),
                 ('burst_dmg_single_pct', '5'), ('pierce_dmg_pct', '5'),
                 ('armor_break_dmg_pct', '5'), ('dot_dmg_pct', '5'),
                 ('projectile_explosion_dmg_pct', '5'), ('projectile_attachment_dmg_pct', '5'),
                 ('sequential_dmg_pct', '5'), ('part_dmg_pct', '5'), ('intercept_dmg_pct', '5'),
                 ('split_dmg_pct', '6'), ('element_bonus_pct', '7'), ('reload_speed_pct', 'count')]
        for stat, group in cases:
            with self.subTest(stat=stat):
                out = build_damage_groups({'x': [effect('all_allies', stat)]}, {})['x']['effects'][0]
                self.assertEqual((out['group'], out['scope']), (group, 'ally'))
                self.assertEqual(out['caster_based'], stat == 'atk_caster_based_pct')
        for target, scope in [('self', 'self'), (['self', 'self'], 'self'),
                              (['self', 'allies_top_atk:2'], 'ally'), ('self|allies_weapon:SG', 'ally'),
                              ('receiver', 'ally')]:
            out = build_damage_groups({'x': [effect(target)], 'receiver': []}, {})['x']['effects']
            self.assertEqual(out[0]['scope'], scope)
        for target in ['target', 'same_target:x', 'enemies_top_hp:2', 'all_enemies', 'boss']:
            for stat, group in [('def_pct', '2'), ('def_caster_based_pct', '2'), ('received_dmg_pct', '6')]:
                out = build_damage_groups({'x': [effect(target, stat, polarity='harmful')]}, {})['x']['effects'][0]
                self.assertEqual((out['scope'], out['group']), ('enemy', group))
                self.assertEqual(out['caster_based'], stat == 'def_caster_based_pct')

    def test_skips_and_value_projection(self):
        skipped = [effect('self', 'received_dmg_pct'), effect('all_allies', polarity='harmful'),
                   effect('target', 'received_dmg_pct'), effect('self', 'def_pct'),
                   effect('self', 'projectile_dmg_pct'), effect('self_cover'),
                   effect('all_projectiles'), effect('target', polarity='harmful'),
                   dict(type='damage', stat='atk_pct', target='self')]
        self.assertEqual(build_damage_groups({'x': skipped}, {})['x']['effects'], [])
        values = {'1': 1, '10': 10}
        source = effect(values=values, max_stack=3, favorite=2)
        fixed = effect(fixed_value=-4, max_stack=0)
        unknown = effect(fixed_value='unknown', max_stack=True)
        profiles = build_damage_groups({'x': [source, fixed, unknown]}, {'x': {'favorite_slots': [2, 1]}})
        out = profiles['x']['effects']
        self.assertEqual(profiles['x']['favorite_slots'], [2, 1])
        self.assertEqual(out[0]['values'], values)
        self.assertIsNot(out[0]['values'], values)
        self.assertEqual((out[0]['max_stack'], out[0]['favorite']), (3, 2))
        self.assertEqual((out[1]['fixed'], out[1]['max_stack'], out[1]['favorite']), (-4, 1, None))
        self.assertNotIn('values', out[2]); self.assertNotIn('fixed', out[2])
        self.assertEqual(out[2]['max_stack'], 1)
        instant = dict(type='instant', target='self', stat='burst_reentry')
        self.assertEqual(build_damage_groups({'x': [instant]}, {})['x']['effects'][0]['group'], 'count')

    def test_damage_group_selectors(self):
        for target, kind in [('all_allies', 'all'), ('allies_code:수냉', 'element'),
                             ('allies_top_atk:2', 'dynamic'),
                             ('self|allies_code:수냉', 'element')]:
            entry = build_damage_groups({'x': [effect(target)]}, {})['x']['effects'][0]
            self.assertEqual(entry['selector']['kind'], kind)
            self.assertIn('tier', entry)
        for target, stat, polarity in [('self', 'atk_pct', 'beneficial'),
                                       ('target', 'def_pct', 'harmful')]:
            entry = build_damage_groups({'x': [effect(target, stat, polarity=polarity)]}, {})['x']['effects'][0]
            self.assertNotIn('selector', entry)
            self.assertNotIn('tier', entry)

    def test_real_damage_groups(self):
        data = Path(__file__).resolve().parents[1] / 'research/upstream/nikke-calc-master/data'
        profiles = build_damage_groups(json.loads((data / 'parsed_skills.json').read_text()),
                                       json.loads((data / 'parsed_nikke.json').read_text()))
        self.assertTrue(all(e['group'] in {'1','2','3','4','5','6','7','count'}
                            for p in profiles.values() for e in p['effects']))
        crown = profiles['크라운']['effects']
        self.assertTrue(any(e['stat'] == 'atk_caster_based_pct' and e['group'] == '2'
                            and e['scope'] == 'ally' and e['caster_based']
                            and e['selector']['kind'] == 'all' for e in crown))
        self.assertTrue(any(e['stat'] == 'reload_speed_pct' and e['group'] == 'count' for e in crown))


if __name__ == '__main__':
    unittest.main()
