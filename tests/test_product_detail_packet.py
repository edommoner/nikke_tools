"""Product packet admission and full response comparison without GPU calls."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('product_packet',ROOT/'research/verify-product-detail.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class ProductPacket(unittest.TestCase):
    def test_typed_skill_decoder_uses_exact_static_coefficient_without_research_imports(self):
        import builtins,struct
        from portable_world_result import read_typed_battle
        block=[0]*1048576;block[786432]=0x44425431;block[786433]=1
        block[789250]=1;block[789251]=1;block[789252]=1
        at=790000;block[at:at+4]=[1,0,0,1];block[at+10]=1
        for offset,value in [(4,1.),(6,3.),(8,7.),(22,2.)]:
            block[at+offset:at+offset+2]=struct.unpack('<II',struct.pack('<d',value))
        block[at+16:at+22]=[0,2,10,1,1,0]
        case=dict(typed_bindings=[{}],max_attacks=128,effects=[dict(target='all_projectiles')],owners=[0])
        meta=dict(binding_source_indices=[0]);original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name in ('world_frame_native','world_authored_roster'):
                raise ImportError('Research module deliberately unavailable')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=guarded):
            result=read_typed_battle(block,(case,meta,()),sampled_coefficients=[3.])
            with self.assertRaises(AssertionError):
                read_typed_battle(block,(case,meta,()),sampled_coefficients=[4.])
        self.assertEqual(result['attacks'][0]['damage'],7.)
        self.assertEqual(result['attacks'][0]['receipts'][0]['took'],2.)

    def test_weapon_only_typed_decoder_has_no_research_import_dependency(self):
        import builtins,struct
        from portable_world_result import read_typed_battle
        block=[0]*1048576;block[786432]=0x44425431
        block[789250]=1;block[789251]=1;block[789252]=1
        original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name in ('world_frame_native','world_authored_roster','destructible_skill_specs'):
                raise ImportError('Research module deliberately unavailable')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=guarded):
            result=read_typed_battle(block,(dict(typed_bindings=[],max_attacks=128),{},()))
        self.assertEqual(result,dict(time=0.,finished=True,state=[],attacks=[]))

    def test_stationary_world_clock_must_survive_gpu_readback(self):
        from portable_detail import validate_world_frame_readback
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        base=L['WORLD_FRAME_OUTPUT_BASE'];block=[0]*(base+788)
        meta={'product_world_frame_contract':{'nodes':2}}
        with self.assertRaisesRegex(UnsupportedPortable,'clock readback'):
            validate_world_frame_readback(block,meta)
        block[base+1]=1;block[base+784]=32;validate_world_frame_readback(block,meta)
        block[base+16]=1
        with self.assertRaisesRegex(UnsupportedPortable,'clock readback'):
            validate_world_frame_readback(block,meta)

    def test_generated_mutation_snapshot_guard_rejects_the_saved_cuda_failure(self):
        from portable_slang_generation import validate_counter_snapshots
        for field in ('removalCount','carrierCount'):
            for op in ('>','<','>=','<='):
                with self.subTest(field=field,op=op),self.assertRaisesRegex(ValueError,'reflexive'):
                    validate_counter_snapshots('if((_S9502->'+field+'_0) '+op+' (_S9502->'+field+'_0)) {}')
        validate_counter_snapshots('if((_S9502->removalCount_0) > begin_4) {}')
        validate_counter_snapshots('if((_S9502->removalCount_0) > (_S9000->removalCount_0)) {}')

    def test_generated_snapshot_guard_also_checks_preexisting_cached_outputs(self):
        import portable_slang_generation as generation
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);outputs={t:root/t for t in ('cuda','metal')}
            for path in outputs.values():path.write_text('if((_S9502->removalCount_0) > before) {}')
            # Exercise real file validation within the same strict prohibition
            # used by CPU-only workers. Never enter a mocked GPU build API.
            with self.cli().forbid_gpu():
                generation.validate_generated_outputs(outputs)
                outputs['cuda'].write_text('if((_S9502->removalCount_0) > (_S9502->removalCount_0)) {}')
                with self.assertRaisesRegex(ValueError,'reflexive'):
                    generation.validate_generated_outputs(outputs)
                with self.assertRaisesRegex(RuntimeError,'forbidden'):
                    generation.build(root,'test','entry')

    def test_optional_frame_checks_keep_complete_declared_dependencies_in_product_payload(self):
        from portable_cpu_tests import AUDIT_FILES,validate_dependency_files
        included=set(self.cli().SUITES['product-detail']['support_files'])
        validate_dependency_files(ROOT,['test_dispatch_frame_storage.py'],included=included)
        for name in AUDIT_FILES['test_dispatch_frame_storage.py']:
            with self.subTest(missing=name),self.assertRaisesRegex(ValueError,'dependency'):
                validate_dependency_files(ROOT,['test_dispatch_frame_storage.py'],included=included-{name})

    def cli(self):
        spec=importlib.util.spec_from_file_location('product_program_cli',ROOT/'scripts/nikke_gpu.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        return cli
    def test_program_selection_preserves_legacy_and_rejects_unknown_names(self):
        from portable_product_programs import configuration,PROGRAMS
        cli=self.cli();base=cli.SUITES['product-detail']
        self.assertIs(configuration(cli.SUITES,'product-detail'),base)
        self.assertIs(configuration(cli.SUITES,dict(suite='product-detail')),base)
        self.assertEqual(len(PROGRAMS),78)
        self.assertEqual({n for n in PROGRAMS if n.startswith('coordinate-')},{'coordinate-fixed','coordinate-accumulate','coordinate-cover-fixed','coordinate-cover-accumulate','coordinate-weighted-fixed','coordinate-weighted-accumulate','coordinate-add-fixed','coordinate-add-accumulate','coordinate-healing-fixed','coordinate-healing-accumulate'})
        self.assertEqual({n for n in PROGRAMS if n.startswith('healing-') and n.endswith('-group')},
                         {'healing-fixed-group','healing-accumulate-group','healing-cover-fixed-group','healing-cover-accumulate-group'})
        self.assertEqual({n for n in PROGRAMS if n.startswith('movement-range-cover-')},
                         {'movement-range-cover-fixed','movement-range-cover-accumulate'})
        self.assertEqual({n for n in PROGRAMS if n.startswith('ammo-')},{stem+mode+suffix for stem in ('ammo-','ammo-cover-') for mode in ('fixed','accumulate') for suffix in ('','-group','-target')})
        self.assertEqual({n for n in PROGRAMS if n.startswith('default-')},{'default-weighted-fixed','default-cover-fixed'})
        self.assertEqual({n for n in PROGRAMS if n.startswith('cover-')},{'cover-'+mode+suffix for mode in ('accumulate','fixed') for suffix in ('','-group','-target','-group-target')})
        self.assertEqual({n for n in PROGRAMS if n.startswith('weighted-')},{'weighted-fixed','weighted-accumulate','weighted-fixed-group','weighted-accumulate-group'})
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
                self.assertEqual(len(rows),7 if name=='ammo-cover-fixed-group' else 1)
                self.assertEqual((selected.SOURCE,selected.suite.INPUT,selected.suite.OUTPUT),(config['source'],config['input_words'],config['output_words']))
                self.assertEqual(len(raw),4*(1+len(rows)*config['input_words']))
                self.assertEqual(rows[0][2][0]['burst_gauge_mode'],config['mode'])
                self.assertFalse(rows[0][2][1]['cpu_battle_executed'])
                self.assertEqual(rows[0][1][LIMITS['WORLD_CONTROL_INPUT_BASE']+1],6 if config['mode']=='fixed' and name.startswith(('typed-','coordinate-','movement-','named-range-','cover-','default-cover-','healing-cover-','ammo-cover-','lock-cover-')) else 3 if name.startswith(('typed-','coordinate-','cover-','movement-','named-range-','healing-cover-','ammo-cover-','lock-cover-')) else 4 if config['mode']=='fixed' else 1)
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
