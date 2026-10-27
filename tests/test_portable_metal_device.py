"""Device visibility is an early CPU0 gate, never a GPU calculation proof."""
import contextlib,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_metal_device as device
s=importlib.util.spec_from_file_location('metal_device_cli_test',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)

class PlatformNameOnly:
    def __init__(self,name):self.name=name
    def __getattr__(self,name):return getattr(os,name)

class DeviceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'scripts').mkdir();self.script=self.root/'scripts/metal-device-probe.swift';self.script.write_text('// fixture probe')
        self.value=dict(schema='metal-device-visibility-v1',device_visible=True,kernel_calls=0,device='Apple fixture',registry_id='42',max_buffer_length=2**32,os_build='fixture OS build')
    def context(self):
        stack=contextlib.ExitStack();stack.enter_context(patch.object(device.sys,'platform','darwin'));stack.enter_context(patch.object(device.shutil,'which',return_value='/usr/bin/swift'));stack.enter_context(patch.dict(os.environ,{'NIKKE_METAL_MODULE_CACHE':str(self.root/'modules')}));return stack
    def response(self,code=0,value=None):return subprocess.CompletedProcess([],code,json.dumps(self.value if value is None else value),'')
    def test_visible_device_is_only_an_advisory_and_bounded_without_shell(self):
        with self.context(),patch.object(device.subprocess,'run',return_value=self.response()) as run:r=device.probe(self.root)
        self.assertTrue(r['passed']);self.assertTrue(r['device_visible']);self.assertFalse(r['calculation_verified']);self.assertFalse(r['context_current_verified']);self.assertEqual(r['gpu_calls'],0)
        self.assertEqual(r['os_build'],'fixture OS build')
        argv=run.call_args.args[0];self.assertEqual(argv,['/usr/bin/swift','-module-cache-path',str(self.root/'modules'),str(self.script.resolve())])
        self.assertEqual(run.call_args.kwargs['timeout'],20);self.assertNotIn('shell',run.call_args.kwargs)
    def test_no_device_has_no_success_identity(self):
        with self.context(),patch.object(device.subprocess,'run',return_value=self.response(2,dict(schema='metal-device-visibility-v1',device_visible=False,kernel_calls=0))):r=device.probe(self.root)
        self.assertFalse(r['passed']);self.assertFalse(r['device_visible']);self.assertNotIn('device',r)
    def test_invalid_payload_or_failed_process_never_becomes_visible(self):
        for value,code in [([],0),(dict(self.value,kernel_calls=1),0),(dict(self.value,device_visible=1),0),(dict(self.value,registry_id=''),0),(self.value,1)]:
            with self.subTest(value=value),self.context(),patch.object(device.subprocess,'run',return_value=self.response(code,value)):
                r=device.probe(self.root);self.assertFalse(r['passed']);self.assertIn('error',r)
    def test_timeout_and_missing_toolchain_preserve_failure(self):
        with self.context(),patch.object(device.subprocess,'run',side_effect=subprocess.TimeoutExpired(['swift'],20)):
            r=device.probe(self.root);self.assertFalse(r['passed']);self.assertIn('TimeoutExpired',r['error'])
        with self.context(),patch.object(device.shutil,'which',return_value=None),patch.object(device.subprocess,'run') as run:
            self.assertFalse(device.probe(self.root)['passed']);run.assert_not_called()
    def test_source_mutation_is_rejected(self):
        def changed(*args,**kwargs):self.script.write_text('// changed');return self.response()
        with self.context(),patch.object(device.subprocess,'run',side_effect=changed):r=device.probe(self.root)
        self.assertFalse(r['passed']);self.assertIn('source changed',r['error'])
    def test_non_macos_and_relative_cache_never_start_process(self):
        with self.context(),patch.object(device.sys,'platform','linux'),patch.object(device.subprocess,'run') as run:
            self.assertFalse(device.probe(self.root)['passed']);run.assert_not_called()
        with self.context(),patch.dict(os.environ,{'NIKKE_METAL_MODULE_CACHE':'relative'}),patch.object(device.subprocess,'run') as run:
            self.assertFalse(device.probe(self.root)['passed']);run.assert_not_called()
    def gate_context(self,platform_name=None):
        from portable_wire_layout import metal_guard
        (self.root/'scripts/run-metal-probe.swift').write_text(metal_guard()+'\n')
        name=platform_name or os.name
        compiler=self.root/('slang-'+name)/'bin';compiler.mkdir(parents=True,exist_ok=True)
        (compiler/('slangc.exe' if name=='nt' else 'slangc')).write_text('fixture')
        stack=contextlib.ExitStack();stack.enter_context(patch.object(cli,'ROOT',self.root));stack.enter_context(patch.object(cli,'verify_package',return_value=dict(suite='coordinate-mode-actions',purpose='sealed',package_id='fixture')))
        stack.enter_context(patch.object(cli,'os',PlatformNameOnly(name)))
        stack.enter_context(patch.dict(os.environ,{'NIKKE_SLANG_ROOT':str(compiler.parent)}));stack.enter_context(patch.object(cli,'validate_generation_request'));stack.enter_context(patch.object(cli,'capture_storage_preflight'));stack.enter_context(patch.object(cli,'required_generation_cache_preflight',return_value=False));return stack
    def test_no_device_stops_before_cpu_native_transport_and_claim(self):
        for name in ('posix','nt'):
            capture=self.root/('capture-'+name)
            with self.subTest(platform=name),self.gate_context(name),patch.object(device,'probe',return_value=dict(passed=False,gpu_calls=0)),patch.object(cli,'cpu_test_groups') as tests,patch.object(cli,'cpu_preflight') as native,patch.object(cli,'run_job') as job:
                with self.assertRaisesRegex(RuntimeError,'before CPU preparation'):cli.run_capture(capture,'metal',180)
                tests.assert_not_called();native.assert_not_called();job.assert_not_called()
            self.assertFalse((self.root/'gpu-claimed-metal.json').exists());self.assertFalse(cli.load(capture/'metal-device-preflight.json')['passed'])
            self.assertEqual(cli.load(capture/'run.json')['status'],'failed')
    def test_cpu_only_and_smoke_do_not_query_metal(self):
        for label,kwargs in [('cpu',dict(cpu_only=True)),('smoke',dict(smoke=True))]:
            with self.gate_context(),patch.object(cli,'metal_device_preflight') as probe,patch.object(cli,'cpu_test_groups',side_effect=ValueError('test boundary')):
                with self.assertRaisesRegex(ValueError,'test boundary'):cli.run_capture(self.root/label,'metal',180,**kwargs)
                probe.assert_not_called()

if __name__=='__main__':unittest.main()
