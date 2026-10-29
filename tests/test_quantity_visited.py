"""Shared membership probe: first-seen order, word boundaries and reset."""
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app','research')]
spec = importlib.util.spec_from_file_location('quantity_visited_test_probe', ROOT / 'research/verify-quantity-visited.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class QuantityVisitedTests(unittest.TestCase):
    def test_exact_storage_delta_recovers_all_original_numeric_and_query_bytes(self):
        import json,hashlib
        data=json.loads((ROOT/'tests/fixtures/quantity-visited-source-change-v1.json').read_text())
        row=data['files']['gpu/quantity_runtime.slang']
        source=(ROOT/'gpu/quantity_runtime.slang').read_text()
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),row['after_sha256'])
        for hunk in reversed(row['hunks']):
            self.assertEqual(source.count(hunk['after']),1)
            source=source.replace(hunk['after'],hunk['before'],1)
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),row['before_sha256'])
        self.assertEqual(row['before_sha256'],'d04e568983cc1be4124d5144239cbde63826f51a05c23ba2c7bbb03a0a809020')
        self.assertFalse(data['normalizer_changed'])

    def test_all_groups_word_boundaries_reset_and_every_output_word(self):
        rows, raw = probe.prepare()
        self.assertEqual(len(rows),16)
        self.assertEqual(sum(domain is not None for _,_,domain in rows),9)
        self.assertEqual(len(raw),4+16*516*4)
        for name, words, domain in rows:
            expected = probe.native_reference(words)
            self.assertEqual(probe.compare(expected,words),expected)
            if domain is None:probe.validate_rejection(expected,name)
            for at in (0,4,16,1040,1055):
                bad = list(expected); bad[at] ^= 1
                with self.subTest(name=name,at=at),self.assertRaises(AssertionError):probe.compare(bad,words)
        full = probe.native_reference(rows[6][2])
        self.assertEqual(full[4:6],[256,256])
        self.assertEqual(full[1040:1056],[0xffffffff]*16)
        self.assertEqual(full[16:272],full[528:784])
        self.assertEqual([probe.native_reference(r[1])[0] for r in rows],[0]*9+[64]*7)

    def test_actual_quantity_runtime_uses_shared_helper_without_changing_old_numeric_body(self):
        import json,hashlib
        data=json.loads((ROOT/'tests/fixtures/portable-max-ammo-scaling-source-delta.json').read_text())
        source=(ROOT/'gpu/quantity_runtime.slang').read_text()
        self.assertEqual(data['sources']['gpu/quantity_runtime.slang']['current'],source)
        self.assertEqual(data['added_sources']['gpu/quantity_visited.slang'],hashlib.sha256((ROOT/'gpu/quantity_visited.slang').read_bytes()).hexdigest())
        self.assertIn('QuantityVisited seen;',source)
        self.assertNotIn('uint seen[P_DEFINITIONS]',source)
        self.assertEqual(source.count('seen.insert(group)'),2)
        self.assertIn('#include "quantity_visited.slang"',(ROOT/probe.SOURCE).read_text())
        from portable_max_ammo_scaling_source_contract import project_sources
        projected=project_sources(ROOT)
        self.assertEqual(projected['gpu/quantity_runtime.slang'],data['sources']['gpu/quantity_runtime.slang']['baseline'])
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/quantity_visited.slang':(ROOT/'gpu/quantity_visited.slang').read_text()+'\n'})

if __name__=='__main__':unittest.main()
