"""HP attack basis is first specified against native execution, without GPU packing."""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'research', 'scripts')]
import portable_runtime
import detail_gpu
import engine_worker
from calculator import timeline
from portable_skill_hp_basis_cases import fixtures
from portable_skill_hp_basis_contracts import verify
import world_skill_hp_basis_native as observer
from world_parts_skill_native import observe as plain_observe

spec = importlib.util.spec_from_file_location('hp_basis_reference_cli', ROOT / 'scripts/nikke_gpu.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class SkillHPBasisReferenceTests(unittest.TestCase):
    def test_conditional_protection_repairs_change_subsequent_absorption(self):
        from portable_skill_hp_basis_protection_cases import fixtures as repairs
        with cli.forbid_gpu(), patch.object(portable_runtime,'compile_program',side_effect=AssertionError('packing forbidden')):
            for case in repairs():
                with self.subTest(case=case['name']):
                    native,_=observer.observe(case);self.assertTrue(verify(case,native)['verified'])
                    changed=copy.deepcopy(native);changed['hits'][1][case['contract']['protection_absorption']['kind']]=100
                    with self.assertRaises(AssertionError):verify(case,changed)
    def test_literal_contracts_without_packing_or_gpu(self):
        def forbidden(*args, **kwargs):
            raise AssertionError('GPU/packing forbidden in native contracts')
        with patch.object(timeline, 'simulate', forbidden):
            cases = fixtures()
        self.assertEqual(len(cases), 28)
        before = copy.deepcopy(cases)
        gaps = []
        with cli.forbid_gpu(), patch.object(portable_runtime, 'compile_program', forbidden), patch.object(detail_gpu, 'compile_effects', forbidden), patch.object(detail_gpu, 'compile_full', forbidden):
            for case in cases:
                with self.subTest(case=case['name']):
                    native, _ = observer.observe(case)
                    result = verify(case, native)
                    self.assertTrue(result['verified'])
                    if result['reference_model_gap']:
                        gaps.append(case['name'])
        self.assertEqual(gaps, ['skill-hp-basis-add-deferred', 'skill-hp-basis-replace-deferred'])
        self.assertEqual(cases, before)

    def test_observer_preserves_all_existing_fields_and_trace(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                expected, trace = plain_observe(case)
                actual, observed = observer.observe(case)
                actual.pop('skill_hp_basis_queries')
                self.assertEqual(actual, expected)
                self.assertEqual(observed, trace)

    def test_wrong_totals_packet_maximum_owner_time_or_missing_query_rejected(self):
        case = next(c for c in fixtures() if c['name'] == 'skill-hp-basis-add')
        native, _ = observer.observe(case)
        for fault in ('total', 'packet', 'maximum', 'owner', 'time', 'query-count'):
            changed = copy.deepcopy(native)
            if fault == 'total':
                changed['damage'][0] += 1
            elif fault == 'packet':
                next(p for p in changed['parts_skill_events'] if p['kind'] == 'packet')['damage'] += 1
            elif fault == 'query-count':
                changed['skill_hp_basis_queries'].clear()
            else:
                changed['skill_hp_basis_queries'][0][fault] += 1
            with self.subTest(fault=fault), self.assertRaises(AssertionError):
                verify(case, changed)

    def test_lifesteal_hp_fault_rejected(self):
        case = next(c for c in fixtures() if c['name'] == 'skill-hp-basis-replace-lifesteal')
        native, _ = observer.observe(case)
        native['allies'][0]['hp'] += 1
        with self.assertRaises(AssertionError):
            verify(case, native)

    def test_rounding_grouping_and_parent_snapshot_have_distinct_witnesses(self):
        cases = {c['name']: c for c in fixtures()}
        grouping = cases['skill-hp-basis-add-flat-grouping']
        self.assertEqual(grouping['contract']['damage'][0], 4)
        rounding = cases['skill-hp-basis-replace-multiply-before-divide']
        self.assertEqual(rounding['contract']['damage'][0], 2)
        parent = cases['skill-hp-basis-add-callback-snapshot']
        native, _ = observer.observe(parent)
        self.assertTrue(verify(parent, native)['verified'])
        self.assertEqual(len(native['skill_hp_basis_queries']), 1)
        self.assertEqual(parent['contract']['packets'], [2500, 2500])
        self.assertEqual(parent['contract']['damage'][0], 6800)

    def test_profile_composes_and_restores_after_success_and_failure(self):
        previous = sys.getprofile()
        calls = []
        def prior(frame, event, answer):
            if event == 'return' and frame.f_code is observer.BuffManager.effective_max_hp.__code__:
                calls.append(event)
        try:
            sys.setprofile(prior)
            observer.observe(fixtures()[1])
            self.assertTrue(calls)
            self.assertIs(sys.getprofile(), prior)
            with patch.object(observer, 'parts_observe', side_effect=RuntimeError('injected native failure')):
                with self.assertRaisesRegex(RuntimeError, 'injected native failure'):
                    observer.observe(fixtures()[1])
            self.assertIs(sys.getprofile(), prior)
        finally:
            sys.setprofile(previous)


if __name__ == '__main__':
    unittest.main()
