"""Private numeric-query metadata, scratch allocation and reversible source guards."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_specs import LIMITS as L,shader_schema
from portable_native_query_source_contract import ledger,project_sources,baseline_source
from portable_ordered_history_source_contract import project_sources as project_history
from portable_definition_view_contract import verify


class NativeQueryTests(unittest.TestCase):
    def test_metadata_and_nonoverlapping_cache(self):
        spec=importlib.util.spec_from_file_location('late_query_test',ROOT/'research/verify-world-late-attack-random-short.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        entries,_=module.prepare()
        self.assertEqual((len(entries),sum(domain is not None for _,_,domain in entries)),(19,11))
        for name,_,domain in entries[11:]:
            self.assertIsNone(domain);module.validate_rejection([64],name)
            with self.assertRaises(AssertionError):module.validate_rejection([0],name)
        tags=[w[L['RECIPIENT_META_BASE']+5] for _,w,_ in entries[:11]]
        self.assertEqual(tags,[0x4e515231]*3+[0,0x4e515231,0x4e515231,0x4e515231,0x4e515231,0x4e515231,0x4e515231,0x4e515231])
        self.assertEqual([w[L['RECIPIENT_META_BASE']+6] for _,w,_ in entries[:11]],[0]*7+[1,0,1,1])
        self.assertEqual(L['NATIVE_QUERY_WORDS'],32+64*136)
        from portable_scratch_layout import verify
        self.assertTrue(verify(L)['verified'])
        self.assertLessEqual(L['NATIVE_QUERY_BASE']+L['NATIVE_QUERY_HEADER_WORDS'],786416)
        self.assertEqual((ROOT/'gpu/portable_schema.slang').read_text(),shader_schema())

    def test_each_new_source_delta_is_exact_and_faults_rejected(self):
        project_sources(ROOT)
        projected,_=project_history(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            source=projected.get(name,(ROOT/name).read_text())
            for change in row['changes']:
                self.assertEqual(source.count(change['current']),1)
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    baseline_source(ROOT,name,source.replace(change['current'],change['baseline'],1),history_projected=True)


if __name__=='__main__':unittest.main()
