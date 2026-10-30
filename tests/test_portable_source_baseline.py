"""Source-only development proof cannot borrow unrelated or sealed evidence."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_slang_generation import source_hashes
from portable_source_baseline import check,inventory

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
    def test_active_product_program_uses_its_own_development_source(self):
        from portable_product_programs import GOLDEN
        source='gpu/product_fixed_battle_entry.slang'
        (self.root/source).write_text('// fixed product source fixture; no calculation proof\n')
        table=self.root/GOLDEN;table.parent.mkdir();table.write_text(json.dumps(dict(schema=1,programs={})))
        self.cli.SUITES['product-detail']=dict(self.cli.SUITES['parent'])
        self.manifest.update(suite='product-detail',product_program='fixed',golden=dict(source_sha256=source_hashes(self.root,source)))
        self.packet()
        result=check(self.root,self.cli,'product-detail')
        self.assertEqual(result['product_program'],'fixed')
        self.assertEqual(result['source_sha256'],source_hashes(self.root,source))
        self.assertEqual(result['origin'],'verified-development-closure')
        self.assertFalse(result['registered_source_current']);self.assertFalse(result['calculation_verified'])
        with self.assertRaisesRegex(ValueError,'program differs'):
            check(self.root,self.cli,'product-detail',product_program='accumulate')
        self.cli.verify_package.return_value=dict(self.manifest,purpose='sealed')
        with self.assertRaisesRegex(ValueError,'independently sealed'):
            check(self.root,self.cli,'product-detail')

    def test_inventory_includes_sealed_product_members_and_detects_their_stale_source(self):
        from portable_product_programs import GOLDEN
        source='gpu/product_fixed_battle_entry.slang';(self.root/source).write_text('// fixed source\n')
        self.cli.SUITES['product-detail']=dict(self.cli.SUITES['parent'])
        path=self.root/GOLDEN;path.parent.mkdir()
        path.write_text(json.dumps(dict(schema=1,programs={'fixed':dict(source_sha256=source_hashes(self.root,source))})))
        result=inventory(self.root,self.cli)
        self.assertEqual(result['registered_programs'],1)
        row=next(r for r in result['rows'] if r.get('product_program')=='fixed')
        self.assertEqual(row['status'],'current');self.assertTrue(result['all_registered_source_current'])
        (self.root/source).write_text('// changed fixed source\n')
        result=inventory(self.root,self.cli);row=next(r for r in result['rows'] if r.get('product_program')=='fixed')
        self.assertEqual(row['status'],'stale');self.assertFalse(result['all_registered_source_current'])
        self.assertEqual(result['registered_names'],len(self.cli.SUITES))

    def test_unknown_suite_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):check(self.root,self.cli,'invented')
    def test_inventory_groups_aliases_and_excludes_nonregistered_profiles(self):
        self.cli.SUITES['cached-parent']=dict(self.cli.SUITES['parent'])
        self.cli.SUITES['development']=dict(self.cli.SUITES['parent'],development_only=True)
        self.cli.SUITES['compiler']=dict(self.cli.SUITES['parent'],compiler_only=True)
        r=inventory(self.root,self.cli)
        self.assertEqual((r['baseline_pairs'],r['registered_names']),(3,4))
        self.assertEqual(r['counts'],dict(current=3,stale=0,unavailable=0));self.assertTrue(r['all_registered_source_current'])
        self.assertFalse(r['calculation_verified']);self.assertEqual(r['native_battle_calls'],0)
        self.cli.verify_package.assert_not_called()
    def test_inventory_reports_stale_and_absent_or_malformed_goldens(self):
        self.stale();(self.root/'unrelated.json').unlink();(self.root/'child.json').write_text('[]')
        r=inventory(self.root,self.cli)
        self.assertEqual(r['counts'],dict(current=0,stale=1,unavailable=2));self.assertFalse(r['all_registered_source_current'])
        self.assertEqual(next(x for x in r['rows'] if x['status']=='stale')['changed_files'],['gpu/parent.slang'])
    def test_inventory_hashes_each_source_once_for_different_baselines(self):
        (self.root/'alternate.json').write_bytes((self.root/'parent.json').read_bytes())
        self.cli.SUITES['alternate']=dict(source='gpu/parent.slang',golden='alternate.json')
        with patch('portable_source_baseline.source_hashes',wraps=source_hashes) as hashes:
            r=inventory(self.root,self.cli)
        self.assertEqual(hashes.call_count,3);self.assertEqual(r['baseline_pairs'],4)
    def test_inventory_does_not_claim_global_coverage_from_a_packet(self):
        self.packet()
        with self.assertRaisesRegex(ValueError,'producer checkout'):inventory(self.root,self.cli)
    def test_empty_inventory_is_not_all_current(self):
        self.cli.SUITES={};r=inventory(self.root,self.cli)
        self.assertEqual(r['baseline_pairs'],0);self.assertFalse(r['all_registered_source_current'])

if __name__=='__main__':unittest.main()
