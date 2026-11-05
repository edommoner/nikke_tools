"""The UI merge may enter history only through exact reviewed bytes."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
import portable_cpu_only_source_contract as contract


class UiMergeSourceContractTests(unittest.TestCase):
    def test_exact_inverse_composes_with_unchanged_cpu_history(self):
        rows = json.loads((ROOT / 'tests/fixtures/portable-ui-merge-source-delta.json').read_bytes())['files']
        for name, row in rows.items():
            with self.subTest(name=name):
                final = (ROOT / name).read_bytes()
                before = zlib.decompress(base64.b85decode(row['before_zlib_b85']))
                self.assertEqual(hashlib.sha256(before).hexdigest(), row['before_sha256'])
                self.assertEqual(contract._ui_merge_before(ROOT, name, final), before)
                self.assertEqual(contract.reviewed_bytes(ROOT, name, final), contract.reviewed_bytes(ROOT, name, before))
                final_text = final.decode().replace('\r\n', '\n')
                before_text = before.decode().replace('\r\n', '\n')
                self.assertEqual(contract._ui_merge_before(ROOT, name, final_text.encode(), text=True), before_text.encode())
                self.assertEqual(contract.reviewed_text(ROOT, name, final_text), contract.reviewed_text(ROOT, name, before_text))

    def test_unknown_mutations_are_not_admitted(self):
        for name in contract.UI_MERGE_AFTER_SHA256:
            raw = (ROOT / name).read_bytes()
            with self.subTest(name=name):
                for changed in (raw + b'\n', b'# unreviewed\n' + raw):
                    self.assertEqual(contract._ui_merge_before(ROOT, name, changed), changed)
                    text = changed.decode().replace('\r\n', '\n')
                    self.assertEqual(contract._ui_merge_before(ROOT, name, text.encode(), text=True), text.encode())

    def test_changed_ledger_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / 'tests/fixtures/portable-ui-merge-source-delta.json'
            fixture.parent.mkdir(parents=True)
            fixture.write_bytes((ROOT / fixture.relative_to(root)).read_bytes() + b'\n')
            name = 'app/engine_worker.py'
            with self.assertRaisesRegex(ValueError, 'UI merge source ledger changed'):
                contract._ui_merge_before(root, name, (ROOT / name).read_bytes())

    def test_changed_preimage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'historical preimage changed'):
            contract._before(base64.b85encode(zlib.compress(b'changed')), '0' * 64)
