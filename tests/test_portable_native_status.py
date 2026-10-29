"""A numerical overflow proof cannot admit error statuses for other suites."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_native_status import expected

class NativeStatusTests(unittest.TestCase):
    def test_legacy_battle_stays_status_zero_without_asking_an_adapter(self):
        adapter=SimpleNamespace(native_reference=Mock(side_effect=AssertionError('No status hook for legacy battle')))
        self.assertEqual(expected(adapter,dict(source='gpu/legacy.slang'),object()),0)
        adapter.native_reference.assert_not_called()
    def test_only_registered_numerical_failure_contract_accepts_exact_integer_status(self):
        config=dict(source='gpu/enemy_movement_math_probe.slang',native_status_contract='movement-step-overflow-v1')
        for value in (0,16):self.assertEqual(expected(SimpleNamespace(native_reference=lambda _:dict(status=value)),config,None),value)
        for value in (True,False,64,2,-1,'16',None):
            with self.assertRaises(ValueError):expected(SimpleNamespace(native_reference=lambda _:dict(status=value)),config,None)
        for changed in (dict(config,source='gpu/world_coordinate_resident_frames_entry.slang'),dict(config,native_status_contract='all-errors')):
            with self.assertRaises(ValueError):expected(SimpleNamespace(native_reference=lambda _:dict(status=16)),changed,None)
if __name__=='__main__':unittest.main()
