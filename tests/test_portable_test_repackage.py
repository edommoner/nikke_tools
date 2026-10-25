"""Only test updates may bypass baseline construction, never runtime gates."""
import contextlib,copy,importlib.util,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_test_repackage import refresh,OLD_LAUNCHER,LAUNCHER
s=importlib.util.spec_from_file_location('refresh_test_api',ROOT/'scripts/nikke_gpu.py');api=importlib.util.module_from_spec(s);s.loader.exec_module(api)

class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);r=Path(self.tmp.name);self.source=r/'source';self.workspace=r/'workspace';self.capture=r/'capture';self.output=r/'new.zip'
        self.prefix='VALUE=1\ndef main():pass\n'
        data={'scripts/nikke_gpu.py':(self.prefix+OLD_LAUNCHER).encode(),'gpu/shared.slang':b'// unchanged shader','app/model.py':b'# unchanged native','tests/test_gate.py':b'pass\n'}
        for root in (self.source,self.workspace):
            for name,raw in data.items():p=root/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(raw)
        (self.workspace/'scripts/nikke_gpu.py').write_text(self.prefix+LAUNCHER);(self.workspace/'tests/test_gate.py').write_text('assert True\n')
        self.m=dict(schema=api.SCHEMA,suite='fixture',purpose='development',selected_cases=[],files=api.file_records(self.source,list(data)),golden=dict(input_sha256='0'*64,source_sha256={'gpu/shared.slang':api.sha(data['gpu/shared.slang'])},entries=[dict(name='case',native_sha256='1'*64)]))
        self.m['package_id']=api.package_id(self.m);api.write(self.source/'gpu-package.json',self.m)
        self.capture.mkdir();api.write(self.capture/'run.json',dict(package_id=self.m['package_id'],mode='gpu',status='failed'));api.write(self.capture/'artifacts.json',dict(files=api.file_records(self.capture,['run.json'])))
    def run_refresh(self,tests=None):
        with patch.object(api,'verify_saved_package',return_value=copy.deepcopy(self.m)):
            return refresh(api,self.source,self.capture,self.workspace,['tests/test_gate.py'] if tests is None else tests,self.output)
    def test_new_identity_preserves_every_non_test_byte_and_all_goldens(self):
        before=(self.source/'gpu-package.json').read_bytes();result=self.run_refresh()
        self.assertTrue(result['passed']);self.assertEqual(result['gpu_calls'],0);self.assertFalse(result['calculation_verified']);self.assertNotEqual(result['package_id'],self.m['package_id'])
        with zipfile.ZipFile(self.output) as z:
            m=json.loads(z.read('gpu-package.json'));self.assertEqual(m['golden'],self.m['golden']);self.assertEqual(m['package_id'],api.package_id(m))
            for row in m['files']:
                name=row['path'];self.assertEqual(z.read(name),(self.workspace/name).read_bytes() if name=='tests/test_gate.py' else (self.source/name).read_bytes())
        self.assertEqual((self.source/'gpu-package.json').read_bytes(),before)
    def test_math_or_cli_core_change_is_rejected(self):
        for name in ('gpu/shared.slang','app/model.py','scripts/nikke_gpu.py'):
            path=self.workspace/name;before=path.read_bytes();path.write_bytes(before.replace(b'VALUE=1',b'VALUE=2') if name.endswith('nikke_gpu.py') else b'changed')
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'Non-test'):self.run_refresh()
            path.write_bytes(before);self.assertFalse(self.output.exists())
    def test_claim_or_started_capture_is_never_refreshed(self):
        for path in (self.source/'gpu-claimed-metal.json',self.capture/'execution.json',self.capture/'readback.bin'):
            path.write_text('original')
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'claim|started'):self.run_refresh()
            self.assertEqual(path.read_text(),'original');path.unlink();self.assertFalse(self.output.exists())
    def test_only_unique_existing_test_python_changes_are_allowed(self):
        for names in ([],['gpu/shared.slang'],['tests/fixture.json'],['tests/../test_gate.py'],['tests/test_missing.py'],['tests/test_gate.py']*2):
            with self.subTest(names=names),self.assertRaises(ValueError):self.run_refresh(names)
        (self.workspace/'tests/test_gate.py').write_bytes((self.source/'tests/test_gate.py').read_bytes())
        with self.assertRaisesRegex(ValueError,'No test content'):self.run_refresh()
    def test_not_failed_or_not_development_is_rejected(self):
        (self.capture/'run.json').write_text(json.dumps(dict(package_id=self.m['package_id'],mode='gpu',status='running')))
        with self.assertRaisesRegex(ValueError,'failed preflight'):self.run_refresh()
        self.m['purpose']='sealed';self.m['package_id']=api.package_id(self.m);(self.source/'gpu-package.json').write_text(json.dumps(self.m))
        with self.assertRaisesRegex(ValueError,'development'):self.run_refresh()
    def test_output_collision_and_late_claim_do_not_publish_or_overwrite(self):
        self.output.write_text('original')
        with self.assertRaises(FileExistsError):self.run_refresh()
        self.assertEqual(self.output.read_text(),'original');self.output.unlink()
        def claimed(*args):
            (self.source/'gpu-claimed-metal.json').write_text('new claim');return copy.deepcopy(self.m)
        with patch.object(api,'verify_saved_package',side_effect=claimed),self.assertRaisesRegex(ValueError,'claim'):
            refresh(api,self.source,self.capture,self.workspace,['tests/test_gate.py'],self.output)
        self.assertFalse(self.output.exists());self.assertFalse(list(self.output.parent.glob('*.partial')))
    def test_registered_cli_routes_paths_under_gpu_forbidden_context(self):
        import portable_backend
        def inspect(*args):
            with self.assertRaisesRegex(RuntimeError,'GPU|forbidden'):
                portable_backend.execute()
            self.assertEqual(args[1:],(self.source,self.capture,ROOT,['tests/test_gate.py'],self.output))
            return dict(passed=True,gpu_calls=0)
        output=io.StringIO()
        with patch('portable_test_repackage.refresh',side_effect=inspect) as called,contextlib.redirect_stdout(output):
            api.main(['refresh-tests','--source-package',str(self.source),'--source-capture',str(self.capture),'--test','tests/test_gate.py','--out',str(self.output)])
        called.assert_called_once();self.assertEqual(json.loads(output.getvalue()),dict(passed=True,gpu_calls=0))

if __name__=='__main__':unittest.main()
