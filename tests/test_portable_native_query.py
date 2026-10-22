"""Private numeric-query metadata, scratch allocation and reversible source guards."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_specs import LIMITS as L,shader_schema
from portable_native_query_source_contract import ledger,project_sources
from portable_definition_view_contract import verify


class NativeQueryTests(unittest.TestCase):
    def test_metadata_and_nonoverlapping_cache(self):
        spec=importlib.util.spec_from_file_location('late_query_test',ROOT/'research/verify-world-late-attack-random-short.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        entries,_=module.prepare()
        self.assertEqual((len(entries),sum(domain is not None for _,_,domain in entries)),(12,5))
        for name,_,domain in entries[5:]:
            self.assertIsNone(domain);module.validate_rejection([64],name)
            with self.assertRaises(AssertionError):module.validate_rejection([0],name)
        tags=[w[L['RECIPIENT_META_BASE']+5] for _,w,_ in entries[:5]]
        self.assertEqual(tags,[0x4e515231]*3+[0,0x4e515231])
        self.assertEqual(L['NATIVE_QUERY_BASE'],L['FOCUS_STATE_BASE']+L['FOCUS_STATE_WORDS'])
        self.assertLessEqual(L['NATIVE_QUERY_BASE']+L['NATIVE_QUERY_WORDS'],786416)
        self.assertEqual((ROOT/'gpu/portable_schema.slang').read_text(),shader_schema())

    def test_each_new_source_delta_is_exact_and_faults_rejected(self):
        project_sources(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            source=(ROOT/name).read_text()
            for change in row['changes']:
                self.assertEqual(source.count(change['current']),1)
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    verify(ROOT,sources={name:source.replace(change['current'],change['baseline'],1)})


if __name__=='__main__':unittest.main()
