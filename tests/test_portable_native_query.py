"""Private numeric-query metadata, scratch allocation and reversible source guards."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_specs import LIMITS as L,shader_schema


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


if __name__=='__main__':unittest.main()
