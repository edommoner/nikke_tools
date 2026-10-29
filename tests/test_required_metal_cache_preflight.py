"""Cache misses stop before native tests/claim; native child still rechecks hits."""
import contextlib,hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import portable_required_metal_cache as gate
import portable_backend
from portable_metal_cache import key_for
spec=importlib.util.spec_from_file_location('required_metal_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)

class RequiredMetalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'scripts').mkdir();self.consumer=self.root/'scripts/run-metal-probe.swift';self.consumer.write_bytes(b'consumer')
        self.source=self.root/'generated.metal';self.source.write_bytes(b'generated shader')
        self.cache=self.root/'cache';self.cache.mkdir();self.capture=self.root/'capture';self.capture.mkdir()
        self.device=dict(passed=True,device_visible=True,device='Apple fixture',registry_id='42',os_build='current build')
        self.identity=gate.identity(self.source.read_bytes(),self.consumer.read_bytes(),self.device)
        self.key=key_for(self.identity);self.hashes={'gpu/fixture.slang':'anchored'}
        self.manifest=dict(package_id='fixture',suite='fixture',golden=dict(source_sha256=self.hashes))
        self.api=SimpleNamespace(ROOT=self.root,SUITES={'fixture':dict(source='gpu/fixture.slang')},write=cli.write)
    def context(self):
        stack=contextlib.ExitStack();stack.enter_context(patch.dict(os.environ,NIKKE_METAL_PIPELINE_REQUIRED='1',NIKKE_METAL_PIPELINE_CACHE=str(self.cache)))
        stack.enter_context(patch.object(portable_backend,'build',return_value=({'metal':self.source},self.hashes)))
        stack.enter_context(patch.object(portable_backend,'resident_plan',return_value=None))
        stack.enter_context(patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')))
        return stack
    def populate(self):
        data=b'archive';(self.cache/(self.key+'.metalarc')).write_bytes(data)
        (self.cache/(self.key+'.json')).write_text(json.dumps(dict(identity=self.identity,archive_bytes=len(data),archive_sha256=hashlib.sha256(data).hexdigest())))
    def run_gate(self):return gate.preflight(self.api,self.manifest,self.capture,self.device)
    def test_missing_cache_records_failure_without_dispatch_or_native_work(self):
        with self.context(),self.assertRaisesRegex(RuntimeError,'no execution claim consumed'):self.run_gate()
        report=cli.load(self.capture/'metal-cache-preflight.json');self.assertFalse(report['passed']);self.assertEqual(report['cache']['key'],self.key);self.assertEqual(report['gpu_calls'],0)
    def test_hit_is_advisory_and_requires_native_revalidation(self):
        self.populate()
        with self.context():self.assertTrue(self.run_gate())
        report=cli.load(self.capture/'metal-cache-preflight.json');self.assertTrue(report['passed']);self.assertTrue(report['native_cache_revalidation_required']);self.assertFalse(report['calculation_verified'])
    def test_corrupt_archive_or_metadata_is_not_a_hit(self):
        self.populate();(self.cache/(self.key+'.metalarc')).write_bytes(b'Archive')
        with self.context(),self.assertRaises(RuntimeError):self.run_gate()
        self.populate();(self.cache/(self.key+'.json')).write_text('{}')
        with self.context(),self.assertRaises(RuntimeError):self.run_gate()
    def test_current_os_and_device_are_part_of_key(self):
        self.populate();self.device['os_build']='new OS'
        with self.context(),self.assertRaises(RuntimeError):self.run_gate()
        self.assertNotEqual(cli.load(self.capture/'metal-cache-preflight.json')['cache']['key'],self.key)
    def test_source_mismatch_fails_before_cache_inspection(self):
        self.populate();self.manifest['golden']['source_sha256']={'other':'hash'}
        with self.context(),patch.object(gate,'probe_identity') as probe,self.assertRaisesRegex(RuntimeError,'source identity changed'):self.run_gate()
        probe.assert_not_called()
    def test_optional_mode_never_generates_source(self):
        with patch.dict(os.environ,NIKKE_METAL_PIPELINE_REQUIRED='0'),patch.object(portable_backend,'build') as build:self.assertFalse(self.run_gate())
        build.assert_not_called();self.assertFalse((self.capture/'metal-cache-preflight.json').exists())
    def test_source_generation_failure_is_recorded_without_cache_or_dispatch(self):
        with self.context(),patch.object(portable_backend,'build',side_effect=RuntimeError('generation failed')),patch.object(gate,'probe_identity') as probe,self.assertRaisesRegex(RuntimeError,'generation failed'):self.run_gate()
        probe.assert_not_called();report=cli.load(self.capture/'metal-cache-preflight.json');self.assertEqual(report['source_generation_api_calls'],1);self.assertFalse(report['passed'])
    def test_missing_os_build_is_not_inferred_from_saved_result(self):
        for field in ('os_build','registry_id','device'):
            value=dict(self.device);value.pop(field)
            with self.subTest(field=field),self.assertRaises(ValueError):gate.identity(b's',b'c',value)
    def test_symlink_cache_member_is_rejected(self):
        self.populate();archive=self.cache/(self.key+'.metalarc');target=self.root/'outside';archive.rename(target);archive.symlink_to(target)
        with self.context(),self.assertRaises(RuntimeError):self.run_gate()
    def test_real_run_capture_gate_precedes_tests_native_job_and_claim(self):
        compiler=self.root/'slang/bin';compiler.mkdir(parents=True)
        for name in ('slangc','slangc.exe'):(compiler/name).write_text('fixture')
        for os_name in ('posix','nt'):
            capture=self.root/('cli-capture-'+os_name)
            with self.subTest(os_name=os_name),self.context(),contextlib.ExitStack() as stack:
                # Local proxy selects both executable names without changing
                # pathlib's host OS or bypassing the real device gate.
                stack.enter_context(patch.object(cli,'os',SimpleNamespace(**dict(vars(os),name=os_name))))
                for name,value in [('ROOT',self.root),('verify_package',lambda root:self.manifest),('SUITES',self.api.SUITES),('validate_generation_request',lambda m:None),('capture_storage_preflight',lambda *a,**k:None),('required_generation_cache_preflight',lambda *a:False),('metal_device_preflight',lambda cap:self.device)]:stack.enter_context(patch.object(cli,name,value))
                from portable_wire_layout import metal_guard
                self.consumer.write_text(metal_guard())
                stack.enter_context(patch.dict(os.environ,NIKKE_SLANG_ROOT=str(compiler.parent)))
                with patch.object(cli,'cpu_test_groups') as tests,patch.object(cli,'cpu_preflight') as native,patch.object(cli,'run_job') as job:
                    with self.assertRaisesRegex(RuntimeError,'no execution claim consumed'):cli.run_capture(capture,'metal',180)
                    tests.assert_not_called();native.assert_not_called();job.assert_not_called()
            self.assertFalse((self.root/'gpu-claimed-metal.json').exists());self.assertEqual(cli.load(capture/'run.json')['status'],'failed')

if __name__=='__main__':unittest.main()
