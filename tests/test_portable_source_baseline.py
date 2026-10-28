"""Source-only development proof cannot borrow unrelated or sealed evidence."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_slang_generation import source_hashes
from portable_source_baseline import check

class SourceBaseline(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();(self.root/'gpu').mkdir()
        for name,text in [('common','uint x=1;\n'),('parent','#include "common.slang"\n'),('child','#include "parent.slang"\n'),('unrelated','uint y=2;\n')]:
            (self.root/'gpu'/f'{name}.slang').write_text(text)
        suites={}
        for name in ('parent','child','unrelated'):
            suites[name]=dict(source=f'gpu/{name}.slang',golden=f'{name}.json')
            (self.root/f'{name}.json').write_text(json.dumps(dict(source_sha256=source_hashes(self.root,f'gpu/{name}.slang'))))
        self.cli=SimpleNamespace(SUITES=suites,verify_package=Mock())
        self.manifest=dict(package_id='verified-package',suite='child',purpose='development',golden=dict(source_sha256=source_hashes(self.root,'gpu/child.slang')))
    def stale(self,suite='parent'):
        p=self.root/f'{suite}.json';d=json.loads(p.read_text());d['source_sha256'][f'gpu/{suite}.slang']='0'*64;p.write_text(json.dumps(d))
    def packet(self):
        (self.root/'gpu-package.json').write_text('{}')
        self.cli.verify_package.return_value=copy.deepcopy(self.manifest)
    def test_current_registered_source_is_only_a_source_proof(self):
        r=check(self.root,self.cli,'parent');self.assertTrue(r['registered_source_current'])
        self.assertEqual(r['origin'],'registered-golden');self.assertFalse(r['calculation_verified'])
        self.assertFalse(r['gpu_execution_verified']);self.assertEqual(r['gpu_calls'],0)
        self.cli.verify_package.assert_not_called()
    def test_stale_producer_and_sealed_or_compiler_packets_fail_closed(self):
        self.stale()
        with self.assertRaisesRegex(ValueError,'stale'):check(self.root,self.cli,'parent')
        self.packet()
        for purpose in ('sealed','compiler-diagnostic'):
            self.cli.verify_package.return_value=dict(self.manifest,purpose=purpose)
            with self.subTest(purpose=purpose),self.assertRaisesRegex(ValueError,'stale'):check(self.root,self.cli,'parent')
    def test_verified_development_parent_keeps_historical_baseline_unchanged(self):
        self.stale();self.packet();before=(self.root/'parent.json').read_bytes()
        r=check(self.root,self.cli,'parent')
        self.assertFalse(r['registered_source_current']);self.assertEqual(r['origin'],'verified-development-closure')
        self.assertEqual(r['source_sha256'],source_hashes(self.root,'gpu/parent.slang'))
        self.assertEqual((self.root/'parent.json').read_bytes(),before);self.assertFalse(r['calculation_verified'])
        self.cli.verify_package.assert_called_once_with(self.root)
    def test_unrelated_entry_and_mismatched_shared_dependency_are_rejected(self):
        self.stale('unrelated');self.packet()
        with self.assertRaisesRegex(ValueError,'outside'):check(self.root,self.cli,'unrelated')
        self.stale();bad=copy.deepcopy(self.manifest);bad['golden']['source_sha256']['gpu/common.slang']='1'*64
        self.cli.verify_package.return_value=bad
        with self.assertRaisesRegex(ValueError,'outside'):check(self.root,self.cli,'parent')
    def test_invalid_packet_cannot_hide_behind_a_current_registered_hash(self):
        self.packet();self.cli.verify_package.side_effect=ValueError('Invalid package identity')
        with self.assertRaisesRegex(ValueError,'Invalid package'):check(self.root,self.cli,'parent')
    def test_unknown_suite_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):check(self.root,self.cli,'invented')

if __name__=='__main__':unittest.main()
