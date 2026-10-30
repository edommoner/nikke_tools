"""Same relocatable engine with unchanged full producer PTX, not a new runner."""
import copy,json,os,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import test_portable_partition_object as focus_tests
import portable_partition_object as obj
cli=focus_tests.cli


class ModuleObjectTests(unittest.TestCase):
    def setUp(self):
        self.f=focus_tests.PartitionObjectTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.request=dict(self.f.request,source_kind='module');self.request.pop('candidate')
        # Existing historical-object fixtures represent compiler-only producers.
        self.f.base.base.m.update(suite='compiler-commands',purpose='compiler-diagnostic')
        cli.write(self.f.base.source_package/'gpu-package.json',self.f.base.base.m)

    def sealed_producer(self):
        producer=self.f.base.base.m
        producer.update(suite='moving-group-cache-only',purpose='sealed')
        producer['golden'].update(entries=[dict(name='sealed-fixture')],input_sha256='1'*64,output_sha256='2'*64)
        cli.write(self.f.base.source_package/'gpu-package.json',producer)
        return producer

    def test_sealed_battle_ptx_reuses_full_module_and_preserves_proof_boundary(self):
        self.sealed_producer();origin,raw=self.proof()
        self.assertTrue(origin['producer']['historical_sealed_battle_source'])
        self.assertNotIn('historical_compiler_source',origin['producer'])
        self.assertFalse(origin['producer']['current_battle_equivalence_verified'])
        self.assertEqual(raw,focus_tests.PTX)
        with self.f.context():result=cli.audit_partition_object_capture(self.f.base.m,self.f.capture,verify_artifacts=False,module_object=True)
        self.assertTrue(result['object_verified'],result)
        self.assertFalse(result['link_verified']);self.assertFalse(result['calculation_verified'])

    def test_registered_product_producer_uses_the_same_module_chain(self):
        producer=self.sealed_producer();producer['suite']='product-detail'
        cli.write(self.f.base.source_package/'gpu-package.json',producer)
        origin,raw=self.proof()
        self.assertEqual(raw,focus_tests.PTX)
        self.assertTrue(origin['producer']['historical_sealed_battle_source'])
        self.assertFalse(origin['producer']['current_battle_equivalence_verified'])
        with self.f.context():
            result=cli.audit_partition_object_capture(self.f.base.m,self.f.capture,verify_artifacts=False,module_object=True)
        self.assertTrue(result['object_verified'],result)
        self.assertFalse(result['calculation_verified'])

    def test_product_source_allowlist_does_not_accept_unregistered_or_substituted_entries(self):
        self.assertTrue(cli.registered_battle_source('product-detail'))
        self.assertFalse(cli.registered_battle_source('unregistered-product'))
        with patch.dict(cli.SUITES,{'product-detail':dict(cli.SUITES['product-detail'],source='gpu/product_other_entry.slang')}):
            self.assertFalse(cli.registered_battle_source('product-detail'))
        with patch.dict(cli.SUITES,{'unregistered-product':dict(source='gpu/product_battle_entry.slang')}):
            self.assertFalse(cli.registered_battle_source('unregistered-product'))

    def test_nonsealed_nonworld_or_incomplete_producer_stops_before_native_tool(self):
        producer=self.sealed_producer()
        cases=[(producer,'purpose','development'),(producer,'suite','damage-factors'),(producer['golden'],'entries',[]),(producer['golden'],'entries',{'not':'a list'}),(producer['golden'],'input_sha256',None),(producer['golden'],'output_sha256',None)]
        for target,key,value in cases:
            original=target[key];target[key]=value
            cli.write(self.f.base.source_package/'gpu-package.json',producer)
            with self.subTest(key=key,value=value),self.f.context(),self.assertRaises(ValueError):
                cli.partition_object_origin(self.f.base.m,self.request,module_object=True)
            target[key]=original
        self.assertFalse(self.f.base.processes)

    def test_historical_compiler_and_sealed_battle_modes_are_exclusive(self):
        with self.assertRaisesRegex(ValueError,'exclusive'):
            cli.assembly_origin(self.f.base.m,self.f.base.source_package,self.f.base.producer,historical_compiler=True,sealed_battle_source=True)

    def proof(self):
        f=self.f
        with f.context():
            origin,raw=cli.partition_object_origin(f.base.m,self.request,module_object=True)
            cli.write(f.capture/'object-request.json',dict(self.request,origin=origin));cli.partition_object_child(f.base.m,f.capture,'cuda',module_object=True)
        cli.write(f.capture/'run.json',dict(mode='module-object-only',package_id=f.base.m['package_id'],backend='cuda',memory_limit_mb=2048,status='finished'));f.base.job_proof(f.capture)
        return origin,raw

    def test_original_ptx_all_bytes_and_unique_state_are_not_rewritten(self):
        f=self.f;origin,raw=self.proof()
        self.assertEqual(raw,focus_tests.PTX);self.assertEqual((f.capture/'module.ptx').read_bytes(),focus_tests.PTX)
        self.assertTrue(origin['source_bytes_unchanged']);self.assertFalse(origin['source_partitioned'])
        self.assertFalse(origin['producer']['current_battle_equivalence_verified']);self.assertNotIn('partition_plan_sha256',origin)
        with f.context():r=cli.audit_partition_object_capture(f.base.m,f.capture,verify_artifacts=False,module_object=True)
        self.assertTrue(r['object_verified'],r);self.assertTrue(r['containment_verified']);self.assertFalse(r['preservation_verified']);self.assertFalse(r['link_verified']);self.assertFalse(r['calculation_verified'])
        receipt=cli.load(f.capture/'object.json')['receipt'];self.assertEqual(receipt['identity']['provider'],'diagnostic-module-ptxas');self.assertEqual(receipt['identity']['artifact'],'diagnostic-module-relocatable-object')
        self.assertEqual(receipt['identity']['options'],obj.OPTIONS);self.assertFalse((f.capture/'focus.ptx').exists());self.assertFalse((f.capture/'compiled.cubin').exists())

    def test_cache_or_kind_mismatch_stops_before_compiler(self):
        f=self.f
        with f.context(),self.assertRaisesRegex(ValueError,'source kind'):cli.partition_object_origin(f.base.m,self.request)
        with f.context(),self.assertRaisesRegex(ValueError,'source kind'):cli.partition_object_origin(f.base.m,f.request,module_object=True)
        value=json.loads(f.cache.read_bytes());value['artifact_sha256']='0'*64;f.cache.write_text(json.dumps(value))
        with f.context(),self.assertRaises(ValueError):cli.partition_object_origin(f.base.m,self.request,module_object=True)
        self.assertFalse(f.base.processes)

    def test_audit_cannot_substitute_focus_mode_or_altered_module_object(self):
        f=self.f;self.proof()
        with f.context(),self.assertRaisesRegex(ValueError,'Wrong diagnostic'):cli.audit_partition_object_capture(f.base.m,f.capture,verify_artifacts=False)
        raw=(f.capture/'module.o').read_bytes();(f.capture/'module.o').write_bytes(raw+b'changed')
        with f.context():r=cli.audit_partition_object_capture(f.base.m,f.capture,verify_artifacts=False,module_object=True)
        self.assertFalse(r['object_verified'])

    def test_module_claim_job_flag_and_budget_are_distinct_and_parent_env_restored(self):
        f=self.f;env={'UNRELATED':'preserved'}
        with f.context(),patch.object(cli,'os',types.SimpleNamespace(**dict(vars(os),name='nt',environ=env))),patch.object(cli,'run_job') as job,patch.object(cli,'audit_partition_object_capture',return_value=dict(object_verified=True,calculation_verified=False)):
            args=(60,f.root/'original',f.base.source_package,f.base.producer,f.cache,f.phases,None,f.base.tool)
            cli.partition_object_capture(f.root/'module-run',*args,module_object=True)
            self.assertEqual(job.call_args.kwargs,dict(module_object_only=True));self.assertEqual(job.call_args.args[2],60)
            self.assertTrue((f.base.package/'module-object-claimed-cuda.json').exists());self.assertFalse((f.base.package/'partition-object-claimed-cuda.json').exists());self.assertFalse((f.base.package/'assembly-claimed-cuda.json').exists())
            self.assertNotIn('candidate',cli.load(f.root/'module-run/object-request.json'))
            with self.assertRaises(FileExistsError):cli.partition_object_capture(f.root/'second',*args,module_object=True)
            with self.assertRaises(ValueError):cli.partition_object_capture(f.root/'large',61,*args[1:],module_object=True)
            with self.assertRaisesRegex(ValueError,'must not accept'):cli.partition_object_capture(f.root/'partition',*args[:-2],f.candidate,f.base.tool,module_object=True)
        self.assertEqual(env,{'UNRELATED':'preserved'})

    def test_cli_child_mode_is_explicit_and_mutually_exclusive(self):
        f=self.f;cli.write(f.capture/'start.json',{})
        with f.context(),patch.object(cli,'partition_object_child') as dispatch:
            cli.child(f.capture,'cuda',module_object_only=True);self.assertTrue(dispatch.call_args.kwargs['module_object'])
            with self.assertRaises(ValueError):cli.child(f.capture,'cuda',partition_object_only=True,module_object_only=True)
        with patch.object(cli,'child') as dispatch:cli.main(['_child','--capture',str(f.capture),'--backend','cuda','--module-object-only'])
        self.assertTrue(dispatch.call_args.args[7]);self.assertFalse(dispatch.call_args.args[6])
