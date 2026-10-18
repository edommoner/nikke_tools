import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from effect_overrides import apply_overrides


class EffectOverridesTests(unittest.TestCase):
    def test_delete_and_authored_order_use_stable_definition_identity(self):
        table={'unit':[dict(name='obsolete'),dict(name='capture'),dict(name='overflow')]}
        entries=[dict(character='unit',match={'name':'obsolete'},delete=True),
                 dict(character='unit',match={'name':'capture'},set={'stat':'gauge_charge'}),
                 dict(character='unit',match={'name':'overflow'},move_before={'name':'capture'})]
        result=apply_overrides(table,entries)
        self.assertEqual([e['name'] for e in result['unit']],['overflow','capture']);self.assertEqual(len(table['unit']),3)
        for bad in ({'name':'missing'},{'name':'overflow'}):
            with self.assertRaises(ValueError):apply_overrides(table,[dict(character='unit',match={'name':'overflow'},move_before=bad)])
    def test_capture_data_uses_target_completion_and_preincrement_capacity(self):
        import engine_worker
        from calculator import buff_manager
        effects=buff_manager._PARSED_SKILLS['일레그 : 붐 앤 쇼크'];by_name={e['name']:e for e in effects}
        self.assertEqual(by_name['빙의']['stat'],'target_hit_counter')
        self.assertEqual(by_name['빙의']['target_counter']['world_scope'],'single_body')
        self.assertNotIn('빙의 해제',by_name)
        self.assertLess(effects.index(by_name['고스트 버스터 2']),effects.index(by_name['유령 포획']))
        for name in ('고스트 버스터 2','유령 포획'):
            self.assertEqual(by_name[name]['trigger']['timing'],['event:target_counter_complete:빙의'])
    def test_checked_data_patch_preserves_source_table(self):
        table = {'new unit': [dict(name='consume', stat='gauge_consume', fixed_value=6)]}
        entries = [dict(character='new unit', match=dict(name='consume', fixed_value=6), set={'minimum_remaining': 1})]
        result = apply_overrides(table, entries)
        self.assertEqual(result['new unit'][0]['minimum_remaining'], 1)
        self.assertNotIn('minimum_remaining', table['new unit'][0])
        for bad in ([dict(entries[0], character='missing')],
                    [dict(entries[0], match=dict(name='consume', fixed_value=9))], entries * 2):
            with self.subTest(bad=bad), self.assertRaises(ValueError):apply_overrides(table, bad)
        with self.assertRaises(ValueError):apply_overrides({'new unit': table['new unit'] * 2}, entries)

    def test_installed_data_and_dispatch_preserve_activation_preparation(self):
        import ast
        import engine_worker
        from calculator import buff_manager
        from effect_overrides import install
        before = buff_manager._PARSED_SKILLS
        install()
        self.assertIs(buff_manager._PARSED_SKILLS, before)
        matches = [e for effects in before.values() if isinstance(effects, list) for e in effects if 'minimum_remaining' in e]
        self.assertTrue(matches)
        self.assertTrue(all(e['stat'] == 'gauge_consume' for e in matches))
        # The runtime wrapper retains the dispatcher tree for diagnostics.
        tree = buff_manager.BuffManager._dispatch_instant._nikke_reference_tree
        attrs = [n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)]
        self.assertEqual(attrs.count('consume_resource'), 1)
        self.assertIn('effect_runtime_prepare', attrs)
