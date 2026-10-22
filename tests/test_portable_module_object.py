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
