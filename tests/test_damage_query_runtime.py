import ast
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from damage_query_runtime import DamageQueryScope


class DamageQueryTests(unittest.TestCase):
    def test_scope_is_owner_specific_and_immutable(self):
        names = {'later'}
        scope = DamageQueryScope('a', names)
        names.clear()
        for owner, name, expected in [('a', 'later', True), ('b', 'later', False), ('a', 'earlier', False)]:
            self.assertEqual(scope.excludes(SimpleNamespace(caster=owner, effect={'name': name})), expected)
        with self.assertRaises(FrozenInstanceError):scope.owner = 'b'

    def test_hp_query_filters_sources_without_changing_resident_state(self):
        import engine_worker
        from calculator.buff_manager import BuffManager
        def carrier(owner, name, stat, value=0, flat=0):
            return SimpleNamespace(caster=owner, effect=dict(name=name, stat=stat), target_chars=['a'],
                                   amount=value, hp_bonus_flat=flat)
        active = [carrier('a', 'earlier', 'max_hp_only_pct', 40),
                  carrier('a', 'later', 'max_hp_only_pct', 20),
                  carrier('b', 'later', 'max_hp_only_pct', 10),
                  carrier('a', 'later', 'hp_copy', flat=300),
                  carrier('b', 'later', 'max_hp_from_max_hp_pct', flat=100)]
        manager = SimpleNamespace(state={'base_stats': {'a': {'hp': 1000}}}, _active=active,
                                  _get_value=lambda effect, ab, name: ab.amount,
                                  copy_hp_bonus=lambda ab, name: ab.hp_bonus_flat)
        self.assertEqual(BuffManager.effective_max_hp(manager, 'a'), 2100)
        self.assertEqual(BuffManager.effective_max_hp(manager, 'a', query_scope=DamageQueryScope('a', {'later'})), 1600)
        self.assertIs(manager._active, active)
        self.assertEqual(len(active), 5)

    def test_installed_queries_retain_healing_and_hp_copy_transforms(self):
        import engine_worker
        from calculator import timeline
        from calculator.buff_manager import BuffManager
        from damage_query_runtime import install
        before = timeline.simulate
        install()
        self.assertIs(timeline.simulate, before)
        tree = timeline.simulate._nikke_reference_tree
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertEqual(sum(n.func.attr == 'apply_shared_body_heal' for n in calls), 1)
        self.assertEqual(sum(n.func.attr == 'absorb_heal_storage' for n in calls), 1)
        self.assertEqual(sum(n.func.attr == 'effective_max_hp' and any(k.arg == 'query_scope' for k in n.keywords) for n in calls), 2)
        received = [n for n in calls if n.func.attr == 'heal_received_mult']
        self.assertEqual(len(received), 1)
        self.assertEqual([k.arg for k in received[0].keywords], ['heal_source'])
        hp_tree = BuffManager.effective_max_hp._nikke_reference_tree
        self.assertTrue(any(isinstance(n, ast.Attribute) and n.attr == 'copy_hp_bonus' for n in ast.walk(hp_tree)))


if __name__ == '__main__':unittest.main()
