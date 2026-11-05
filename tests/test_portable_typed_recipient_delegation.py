"""Typed-current-target adapters must delegate compound selectors to native."""
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import enemy_recipient_runtime as recipients


class CompoundDelegationTests(unittest.TestCase):
    def test_list_targets_reach_existing_native_resolver_without_hashing(self):
        target=['all_allies','self'];result=['ally','ally']
        manager=types.SimpleNamespace(_resolve_target=Mock(return_value=result))
        frame=types.SimpleNamespace(target=object())
        runtime=types.SimpleNamespace(event_stack=[frame])
        effect=dict(type='buff',stat='atk_pct',target=target)
        with patch.object(recipients,'state',return_value=runtime),patch.object(recipients,'dynamic_registry',return_value=object()):
            self.assertIs(recipients.resolve_for_effect(manager,effect,target,'owner'),result)
            self.assertIs(recipients.resolve_mutation(manager,effect,'owner'),result)
        self.assertEqual(manager._resolve_target.call_count,2)
        manager._resolve_target.assert_called_with(target,'owner')

    def test_current_scalar_alias_still_uses_generation_aware_scope(self):
        actor=object();registry=types.SimpleNamespace(exact=Mock(return_value=types.SimpleNamespace(label='scoped-enemy')))
        manager=types.SimpleNamespace(_resolve_target=Mock(side_effect=AssertionError('must use scope')))
        frame=types.SimpleNamespace(target=object())
        with patch.object(recipients,'state',return_value=types.SimpleNamespace(event_stack=[frame])),patch.object(recipients,'dynamic_registry',return_value=registry),patch.object(recipients,'logical_enemy',return_value=actor):
            target=next(iter(recipients.CURRENT_TARGETS))
            self.assertEqual(recipients.resolve_mutation(manager,dict(target=target),'owner'),['scoped-enemy'])
            self.assertEqual(recipients.resolve_for_effect(manager,dict(type='buff',stat='atk_pct'),target,'owner'),['scoped-enemy'])
        registry.exact.assert_called_with(actor)


if __name__=='__main__':unittest.main()
