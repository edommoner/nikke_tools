"""Origin preparation retains old evidence and never grants a GPU retry."""
import copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_staged_origin as origin
from portable_staged_preflight import host
import test_portable_staged_failure as failure_fixture
cli=failure_fixture.cli


class StagedOriginTests(unittest.TestCase):
    def setUp(self):
        fixture=failure_fixture.StagedFailureTests();fixture.setUp();self.addCleanup(fixture.doCleanups);self.f=fixture
        c=cli.load(fixture.tx/'transaction.json')
        c.update(transaction=str(fixture.tx),native_indices=[0],backend='cuda',host=host(cli),input=fixture.receipt)
        cli.write(fixture.tx/'transaction.json',c)
        saved=cli.load(fixture.proof/'staged-preflight.json')
        saved.update(schema='staged-native-preflight-v1',package_id=fixture.m['package_id'],host=host(cli),
            transaction_sha256=cli.sha((fixture.tx/'transaction.json').read_bytes()),input_count=1,native_cases=1,
            stage_envelopes=[],original_timeout=None,all_native_preflight_verified=True,calculation_verified=False,gpu_calls=0)
        cli.write(fixture.proof/'staged-preflight.json',saved);self.saved=saved

    def run_check(self,name='origin',mutate=None):
        f=self.f
        def legacy(root,tx,gpu,out):
            self.assertEqual((root,str(tx),gpu),(f.root,str(f.tx),f.proof))
            actual=copy.deepcopy(self.saved)
            if mutate:mutate(actual)
            cli.write(out,actual);return 'old-own-cli admission complete',''
        with patch('portable_continuation_package.owner_snapshot',return_value=dict(manifest=f.m)),patch.object(origin,'readmit',side_effect=legacy),cli.forbid_gpu(),patch.object(cli,'native_value',side_effect=AssertionError('No numerical replay')):
            return origin.check(cli,f.root,f.outer,f.base/name,f.m['package_id'])

    def test_full_failure_plus_own_admission_inventory_does_not_grant_recovery(self):
        f=self.f;before=origin.inventory(cli,[f.root,f.outer,f.tx]);r=self.run_check()
        self.assertTrue(r['passed']);self.assertTrue(r['native_admission_revalidated']);self.assertTrue(r['host_revalidated'])
        for key in ('execution_permitted','recovery_admission_verified','linked_artifact_revalidated','calculation_verified','claims_modified','native_values_reused','environment_preservation_verified'):self.assertIs(r[key],False)
        self.assertEqual((r['native_calls'],r['compiler_calls'],r['gpu_calls']),(0,0,0))
        self.assertEqual(origin.inventory(cli,[f.root,f.outer,f.tx]),before)
        self.assertEqual(cli.sha((f.base/'origin/origin-inventory.json').read_bytes()),r['inventory_sha256'])
        with self.assertRaises(FileExistsError):self.run_check()

    def test_changed_receipt_and_evidence_fail_with_durable_failure(self):
        for kind in ('receipt','file'):
            def mutate(actual):
                if kind=='receipt':actual['native_cases']=0
                else:(self.f.tx/'unexpected.json').write_text('{}')
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.run_check(kind,mutate)
            self.assertFalse(cli.load(self.f.base/kind/'result.json')['passed'])
            self.assertFalse((self.f.base/kind/'origin-inventory.json').exists())
            if kind=='file':(self.f.tx/'unexpected.json').unlink()

    def test_native_count_host_and_boolean_counter_are_not_interchangeable(self):
        for key,value in (('native_cases',True),('input_count',True),('gpu_calls',False),('host',{}),('transaction_nonce','another')):
            row=dict(self.saved,**{key:value})
            with self.subTest(key=key),self.assertRaises(ValueError):origin.validate_admission(cli,self.f.root,self.f.outer,row,self.f.m['package_id'])

    def test_inventory_rejects_links_and_detects_file_addition(self):
        f=self.f;a=origin.inventory(cli,[f.tx]);p=f.tx/'extra';p.write_text('x')
        self.assertNotEqual(origin.inventory(cli,[f.tx]),a);p.unlink()
        p.symlink_to(f.proof/'input.bin')
        with self.assertRaises(ValueError):origin.inventory(cli,[f.tx])

    def test_unreadable_directory_is_not_silently_omitted(self):
        def denied(root,**options):options['onerror'](PermissionError('unreadable evidence'))
        with patch.object(origin.os,'walk',side_effect=denied),self.assertRaises(PermissionError):origin.inventory(cli,[self.f.tx])

    def test_closure_includes_parent_owner_and_bounded_stage_without_workspace(self):
        f=self.f;parent=f.base/'parent';owner=f.base/'parent-owner';outer=f.base/'native';proof=outer/'proof'
        for p in (parent,owner,proof):p.mkdir(parents=True)
        cli.write(owner/'gpu-package.json',dict(package_id='old'))
        cli.write(parent/'transaction.json',dict(transaction=str(parent),package_root=str(owner),package_id='old'))
        c=cli.load(f.tx/'transaction.json');c['resume_parent']=dict(transaction=str(parent));cli.write(f.tx/'transaction.json',c)
        cli.write(outer/'recipe.json',dict(proof_capture=str(proof),original_workspace=str(f.base/'workspace')))
        row=dict(self.saved,stage_envelopes=[dict(capture=str(proof))],original_timeout=dict(capture=str(proof)))
        roots=origin.evidence_roots(cli,f.root,f.outer,row)
        self.assertEqual(set(roots),{f.root,f.outer,f.tx,parent,owner,outer})
        self.assertNotIn(f.base/'workspace',roots)
        c=cli.load(parent/'transaction.json');c['resume_parent']=dict(transaction=str(f.tx));cli.write(parent/'transaction.json',c)
        with self.assertRaises(ValueError):origin.evidence_roots(cli,f.root,f.outer,row)

    def test_output_cannot_land_in_any_original_tree(self):
        f=self.f
        for p in (f.root/'new',f.tx/'new',f.proof/'new'):
            with self.subTest(path=p),self.assertRaises(ValueError):origin.check(cli,f.root,f.outer,p,f.m['package_id'])
            self.assertFalse(p.exists())

    def test_failed_or_timed_out_owner_keeps_its_output_without_replaying(self):
        f=self.f
        for i,error in enumerate((subprocess.CalledProcessError(1,['old-cli'],output='partial receipt',stderr='bad old receipt'),
            subprocess.TimeoutExpired(['old-cli'],120,output=b'partial timeout',stderr=b'timeout detail'))):
            out=f.base/('failed-owner-'+str(i))
            with patch('portable_continuation_package.owner_snapshot',return_value=dict(manifest=f.m)),patch.object(origin,'readmit',side_effect=error) as run,self.assertRaises(type(error)):
                origin.check(cli,f.root,f.outer,out,f.m['package_id'])
            self.assertEqual(run.call_count,1);self.assertFalse(cli.load(out/'result.json')['passed'])
            self.assertIsInstance(cli.load(out/'owner-output.json')['stdout'],str)
            self.assertFalse((out/'origin-inventory.json').exists())

    def test_legacy_process_uses_own_cli_and_never_selects_run_or_native_command(self):
        f=self.f;script=f.root/'scripts/nikke_gpu.py'
        script.write_text('import json,sys,pathlib\nassert sys.argv[1] == "staged-preflight-check"\nassert "--backend" in sys.argv and "cuda" in sys.argv\npathlib.Path(sys.argv[sys.argv.index("--out")+1]).write_text(json.dumps({"own_cli":True}))\nprint("own receipt only")\n')
        out=f.base/'legacy.json';stdout,stderr=origin.readmit(f.root,f.tx,f.proof,out)
        self.assertEqual(cli.load(out),dict(own_cli=True));self.assertEqual(stdout.strip(),'own receipt only');self.assertEqual(stderr,'')

    def test_wrapper_freezes_exact_owner_and_cannot_promote_forged_calculation(self):
        packet=failure_fixture.packet;f=self.f
        request=dict(source_package=str(f.root),source_capture=str(f.outer),expected_package_id=f.m['package_id'])
        plan=packet.recipe('controller',packet.ORIGIN_STAGE,'cuda',f.base/'new',f.base/'workspace',180,request)
        args=packet.proof_arguments(plan)
        self.assertEqual(args[0],'staged-origin-check');self.assertEqual(args[-1],plan['proof_capture'])
        report=self.run_check();self.assertTrue(packet.verified_origin(report,request))
        for key,value in (('calculation_verified',True),('recovery_admission_verified',True),('gpu_calls',False),('package_id','other'),('host_revalidated',False)):
            with self.subTest(key=key):self.assertFalse(packet.verified_origin(dict(report,**{key:value}),request))
        with self.assertRaises(ValueError):packet.recipe('controller',packet.ORIGIN_STAGE,'metal',f.base/'new',None,180,request)

    def test_actual_windows_receipt_preserves_recovery_and_cache_boundaries(self):
        report=json.loads((ROOT/'tests/fixtures/staged-origin-windows-audit-v1.json').read_text())
        stage=json.loads((ROOT/'tests/fixtures/staged-origin-windows-stage-v1.json').read_text())
        self.assertEqual(stage['proof_result'],report);self.assertTrue(stage['stage_verified'])
        self.assertTrue(failure_fixture.packet.verified_origin(report,dict(expected_package_id=report['package_id'])))
        self.assertEqual((report['input_count'],report['native_cases'],report['evidence_roots'],report['evidence_files']),(106,63,34,4916))
        self.assertFalse(report['environment_preservation_verified']);self.assertFalse(stage['calculation_verified'])
        for key in ('execution_permitted','recovery_admission_verified','linked_artifact_revalidated','native_values_reused','claims_modified'):
            self.assertIs(report[key],False)


if __name__=='__main__':unittest.main()
