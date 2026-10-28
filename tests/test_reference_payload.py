"""Full-package registry roots must fail before a broken archive is written."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_reference as reference


class ReferencePayloadTests(unittest.TestCase):
    def test_new_untracked_factory_is_rejected_despite_other_roots(self):
        with patch.object(reference,'REFERENCES',{'new':('new_cases','new_native','new_contracts')}):
            with self.assertRaisesRegex(ValueError,'new:new_cases'):
                reference.validate_reference_payload(['research/new_native.py','research/new_contracts.py'])

    def test_all_roots_required_and_transitive_scope_not_overclaimed(self):
        with patch.object(reference,'REFERENCES',{'new':('new_cases','new_native','new_contracts')}):
            payload=['research/new_cases.py','research/new_native.py','research/new_contracts.py']
            self.assertFalse(reference.validate_reference_payload(payload)['dynamic_import_closure_verified'])
            for path in payload:
                with self.subTest(path=path),self.assertRaises(ValueError):reference.validate_reference_payload(set(payload)-{path})

    def test_shipped_registry_has_real_payload_roots(self):
        payload=[p.relative_to(ROOT).as_posix() for folder in ('app','research') for p in (ROOT/folder).glob('*.py')]
        receipt=reference.validate_reference_payload(payload)
        self.assertEqual(receipt['reference_suites'],len(reference.REFERENCES))
        self.assertTrue(receipt['registry_roots_verified'])


if __name__=='__main__':unittest.main()
