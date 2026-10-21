"""Independent sealing must use a fresh comparison exactly once, never old JSON."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('seal_test_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class SealTests(unittest.TestCase):
    def test_original_comparison_runs_once_and_is_used_without_changes(self):
        result=dict(entries=[dict(native_sha256='fresh')],calculation_verified=True)
        compare=Mock(return_value=result)
        module=SimpleNamespace(compare_readback=compare)
        audit=dict(calculation_verified=True)
        def audited(capture):
            self.assertEqual(capture,'capture')
            self.assertIs(module.compare_readback('manifest',capture),result)
            return audit
        module.audit_capture=audited
        actual,comparison=cli.audited_comparison(module,'capture')
        self.assertIs(actual,audit);self.assertIs(comparison,result)
        compare.assert_called_once_with('manifest','capture')
        self.assertIs(module.compare_readback,compare)

    def test_old_report_or_multiple_comparisons_cannot_be_sealed(self):
        for calls,passed in ((0,True),(2,True),(1,False)):
            compare=Mock(return_value=dict(calculation_verified=passed))
            module=SimpleNamespace(compare_readback=compare)
            def audit(capture):
                for _ in range(calls):module.compare_readback('manifest',capture)
                return dict(calculation_verified=passed)
            module.audit_capture=audit
            with self.subTest(calls=calls,passed=passed),self.assertRaisesRegex(ValueError,'exactly one'):
                cli.audited_comparison(module,'capture')
            self.assertEqual(compare.call_count,calls);self.assertIs(module.compare_readback,compare)

    def test_comparator_failure_is_preserved_and_binding_restored(self):
        compare=Mock(side_effect=ValueError('Raw mismatch'))
        module=SimpleNamespace(compare_readback=compare)
        module.audit_capture=lambda capture:module.compare_readback('manifest',capture)
        with self.assertRaisesRegex(ValueError,'Raw mismatch'):cli.audited_comparison(module,'capture')
        self.assertIs(module.compare_readback,compare)


if __name__=='__main__':unittest.main()
