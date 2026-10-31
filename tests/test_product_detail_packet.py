"""Product packet admission and full response comparison without GPU calls."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('product_packet',ROOT/'research/verify-product-detail.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class ProductPacket(unittest.TestCase):
    def cli(self):
        spec=importlib.util.spec_from_file_location('product_program_cli',ROOT/'scripts/nikke_gpu.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        return cli
    def test_program_selection_preserves_legacy_and_rejects_unknown_names(self):
        from portable_product_programs import configuration,PROGRAMS
        cli=self.cli();base=cli.SUITES['product-detail']
        self.assertIs(configuration(cli.SUITES,'product-detail'),base)
        self.assertIs(configuration(cli.SUITES,dict(suite='product-detail')),base)
        self.assertEqual(len(PROGRAMS),29)
        self.assertEqual({n for n in PROGRAMS if n.startswith('ammo-')},{'ammo-fixed','ammo-accumulate'})
        self.assertEqual({n for n in PROGRAMS if n.startswith('default-')},{'default-weighted-fixed','default-cover-fixed'})
        self.assertEqual({n for n in PROGRAMS if n.startswith('cover-')},{'cover-accumulate'})
        self.assertEqual({n for n in PROGRAMS if n.startswith('weighted-')},{'weighted-fixed','weighted-accumulate'})
        for name in (None,True,[],{},'unknown','fixed/../../anything'):
            with self.subTest(name=name),self.assertRaises(ValueError):
                configuration(cli.SUITES,dict(suite='product-detail',product_program=name))
        with self.assertRaises(ValueError):configuration(cli.SUITES,dict(suite='damage-factors',product_program='fixed'))
        self.assertEqual(cli.SUITES['product-detail'],base)
    def test_each_program_uses_the_actual_static_product_input_and_exact_wire(self):
        from portable_product_programs import PROGRAMS
        from portable_specs import LIMITS
        cli=self.cli()
        with patch.object(adapter.product.engine_worker.sim,'execute',side_effect=AssertionError('No native battle in input preparation')):
            for name,config in PROGRAMS.items():
                selected=cli.open_suite(dict(suite='product-detail',product_program=name))
                rows,raw=selected.prepare()
                self.assertEqual(len(rows),1)
                self.assertEqual((selected.SOURCE,selected.suite.INPUT,selected.suite.OUTPUT),(config['source'],config['input_words'],config['output_words']))
                self.assertEqual(len(raw),4*(1+config['input_words']))
                self.assertEqual(rows[0][2][0]['burst_gauge_mode'],config['mode'])
                self.assertFalse(rows[0][2][1]['cpu_battle_executed'])
                self.assertEqual(rows[0][1][LIMITS['WORLD_CONTROL_INPUT_BASE']+1],3 if name.startswith(('cover-','movement-','named-range-')) else 4 if config['mode']=='fixed' else 1)
                self.assertTrue(cli.registered_battle_source(dict(suite='product-detail',product_program=name)))
    def test_program_baseline_is_explicit_and_unsealed_members_do_not_fall_back(self):
        from portable_product_programs import registered_golden,configuration,GOLDEN
        cli=self.cli();config=configuration(cli.SUITES,dict(suite='product-detail',product_program='fixed'))
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/GOLDEN;path.parent.mkdir()
            for document in [dict(schema=1,programs={}),dict(schema=True,programs={}),dict(schema=1,programs={'unknown':{}}),dict(schema=1,programs={},extra=1)]:
                path.write_text(json.dumps(document))
                with self.assertRaises(ValueError):registered_golden(root,config)
            golden=dict(source_sha256={'gpu/product_fixed_battle_entry.slang':'test-only'},input_sha256='a'*64)
            path.write_text(json.dumps(dict(schema=1,programs={'fixed':golden})))
            self.assertEqual(registered_golden(root,config),golden)
    def test_manifest_program_cannot_be_changed_by_rekeying_the_packet(self):
        from portable_slang_generation import source_hashes
        cli=self.cli()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();(root/'gpu').mkdir()
            (root/'gpu/product_battle_entry.slang').write_bytes(b'// CPU-only packet integrity fixture; no GPU calculation claim\n')
            (root/'gpu/product_fixed_battle_entry.slang').write_bytes(b'#include "product_battle_entry.slang"\n')
            sources=source_hashes(root,'gpu/product_fixed_battle_entry.slang')
            manifest=dict(schema=cli.SCHEMA,suite='product-detail',product_program='fixed',purpose='development',selected_cases=[],files=cli.file_records(root,list(sources)),golden=dict(source_sha256=sources))
            manifest['package_id']=cli.package_id(manifest)
            (root/'gpu-package.json').write_text(json.dumps(manifest))
            self.assertEqual(cli.verify_package(root)['product_program'],'fixed')
            manifest['product_program']='accumulate';manifest['package_id']=cli.package_id(manifest)
            (root/'gpu-package.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'selected kernel'):cli.verify_package(root)
    def test_same_original_static_input_and_source_without_battle(self):
        with patch.object(adapter.product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in preparation')):
            rows,raw=adapter.prepare()
        self.assertEqual(len(rows),1)
        self.assertEqual(len(raw),4*(1+adapter.suite.INPUT))
        self.assertFalse(rows[0][2][1]['cpu_battle_executed'])
        self.assertEqual(adapter.SOURCE,'gpu/product_battle_entry.slang')
        golden=json.loads((ROOT/'research/portable-product-detail-v1-expected.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(raw).hexdigest(),golden['input_sha256'])
    def test_full_comparison_includes_provenance_and_all_product_fields(self):
        for field in ('total_damage','warnings','burst_timeline','evaluator'):
            expected={field:1};actual={field:2}
            with patch.object(adapter,'native_reference',return_value=expected),patch.object(adapter.product,'decode_payload',return_value=actual):
                with self.assertRaisesRegex(ValueError,field):adapter.compare([0]*adapter.suite.OUTPUT,({},None,None,None))
        with patch.object(adapter,'native_reference') as native:
            with self.assertRaisesRegex(ValueError,'Complete'):adapter.compare([],None)
            native.assert_not_called()
        for expected,actual in [({'control':None},{}),({}, {'control':None})]:
            with patch.object(adapter,'native_reference',return_value=expected),patch.object(adapter.product,'decode_payload',return_value=actual):
                with self.assertRaisesRegex(ValueError,'control'):adapter.compare([0]*adapter.suite.OUTPUT,({},None,None,None))
    def test_persistent_hash_ignores_only_environment_vcs_stamp(self):
        a={'evaluator':{'commit':'a'},'total_damage':42,'warnings':['original']}
        b=copy.deepcopy(a);b['evaluator']['commit']='unpacked'
        self.assertEqual(adapter.fingerprint(a),adapter.fingerprint(b))
        for field,value in [('total_damage',43),('warnings',[])]:
            b=copy.deepcopy(a);b[field]=value
            self.assertNotEqual(adapter.fingerprint(a),adapter.fingerprint(b))

if __name__=='__main__':unittest.main()
