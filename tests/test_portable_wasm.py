"""Browser transport fixtures exercise the real evaluator's fresh CPU comparison."""
import base64,copy,gzip,hashlib,json,os,struct,sys,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_detail as detail
import portable_wasm as wasm
from test_portable_native import FIXTURE

class BrowserPhases(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.folder=Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.dict(os.environ,NIKKE_DETAIL_CAPTURE_ROOT=str(self.folder)))
        self.stack.enter_context(patch.object(detail,'execution_environment',return_value={}))
        self.stack.enter_context(patch.object(detail,'prepare',return_value=({},None)))
        self.compiler=self.stack.enter_context(patch.object(detail,'compile_product',return_value=('gpu/test.slang',1,2,[7],{})))
        self.decoder=self.stack.enter_context(patch.object(detail,'decode_payload',return_value={'total_damage':42}))
        self.cpu=self.stack.enter_context(patch.object(detail.engine_worker,'evaluate',side_effect=lambda b:dict(total_damage=42)))
        self.builder=self.stack.enter_context(patch.object(wasm,'build_product',return_value=(None,dict(identity='a'*64))))
        self.body=dict(compute_backend='browser_detail',verify_detail=False)
        self.sha=hashlib.sha256(struct.pack('<2I',1,7)).hexdigest()
    def upload(self,raw=b'\0'*8):
        return dict(input_sha256=self.sha,readback_gzip_base64=base64.b64encode(gzip.compress(raw)).decode(),browser_seconds=.2,device='UA · workers=2 (client-reported)')
    def test_prepare_closes_generator_and_does_not_evaluate_cpu(self):
        rows=detail.prepare_browser_wires([self.body]*32)
        self.assertEqual(len(rows),32);self.assertTrue(all(r['wire']['input_sha256']==self.sha for r in rows))
        self.assertEqual(gzip.decompress(base64.b64decode(rows[0]['wire']['input_gzip_base64'])),struct.pack('<2I',1,7))
        self.cpu.assert_not_called();self.builder.assert_called_once()
        self.assertEqual(len(list(self.folder.glob('*/browser-prepare.json'))),32)
        self.assertEqual(len(list(self.folder.glob('*/input.bin'))),32)
    def test_finish_uses_fresh_cpu_and_honest_evidence(self):
        detail.prepare_browser_wires([self.body]);self.compiler.reset_mock()
        row=detail.finish_browser([self.body],[self.upload()])[0]['result'];c=row['compute']
        self.compiler.assert_called_once();self.cpu.assert_called_once();self.assertTrue(c['cpu_verification']['matched'])
        self.assertEqual(c['backend'],'browser_detail');self.assertTrue(c['browser_execution_reported'])
        self.assertFalse(c['gpu_execution_verified']);self.assertFalse(c['native_execution_verified']);self.assertEqual(c['timing_scope'],'client-reported')
        evidence=json.loads(next(self.folder.glob('*/evidence.json')).read_text());detail.verified_transport(evidence,'browser')
        for key in ('gpu_execution_verified','native_execution_verified'):
            bad=copy.deepcopy(evidence);bad[key]=True
            with self.assertRaises(RuntimeError):detail.verified_transport(bad,'browser')
    def test_sha_length_gzip_and_time_rejected_before_decode(self):
        for changes,reason in [(dict(input_sha256='f'*64),'sha256'),(dict(readback_gzip_base64=self.upload(b'\0'*9)['readback_gzip_base64']),'length'),
            (dict(readback_gzip_base64=self.upload(b'\0'*7)['readback_gzip_base64']),'length'),(dict(readback_gzip_base64='%%%'),'base64'),(dict(browser_seconds=True),'seconds')]:
            with self.subTest(reason=reason):
                row=detail.finish_browser([self.body],[dict(self.upload(),**changes)])[0]['result']
                self.assertEqual(row['compute']['backend'],'cpu');self.assertIn(reason,row['compute']['unsupported'][0]['reason'])
        self.decoder.assert_not_called();self.assertEqual(self.cpu.call_count,5)
    def test_payload_mismatch_returns_cpu(self):
        self.decoder.return_value=dict(total_damage=99)
        result=detail.finish_browser([self.body],[self.upload()])[0]['result']
        self.assertEqual(result['total_damage'],42);self.assertTrue(result['compute']['gpu_result_rejected']);self.cpu.assert_called_once()
    def test_unsupported_passthrough_in_both_phases(self):
        self.compiler.side_effect=detail.UnsupportedPortable('unsupported fixture')
        for rows in (detail.prepare_browser_wires([self.body]),detail.finish_browser([self.body],[None])):
            self.assertEqual(rows[0]['result']['compute']['backend'],'cpu');self.assertNotIn('wire',rows[0])
        self.builder.assert_not_called();self.decoder.assert_not_called()
    def test_caps_and_direct_error(self):
        for bodies in ([],[self.body]*33,[dict(compute_backend='native_detail')]):
            with self.assertRaises(ValueError):detail.prepare_browser_wires(bodies)
        with self.assertRaisesRegex(ValueError,'ジョブ'):detail.evaluate(self.body)
        with self.assertRaisesRegex(ValueError,'ジョブ'):detail.evaluate_many([self.body])
        self.assertEqual(detail.batch_limit([self.body]*32),32)
    def test_cpu_error_is_not_retried(self):
        self.cpu.side_effect=RuntimeError('CPU error')
        result=detail.finish_browser([self.body],[self.upload()])[0]
        self.assertEqual(result,dict(error='CPU error'));self.cpu.assert_called_once()

class WasmBuild(unittest.TestCase):
    def test_real_fixture_identity_and_cache_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'scripts').mkdir()
            for name in ('wasm-product-host.cpp','wasm-platform.h'):(root/'scripts'/name).write_bytes((ROOT/'scripts'/name).read_bytes())
            cpp=root/'kernel.cpp';cpp.write_text(FIXTURE)
            compiler,env=wasm.toolchain(ROOT)
            with patch.object(wasm,'toolchain',return_value=(compiler,env)):
                file,first=wasm.build_wasm(root,cpp);again,second=wasm.build_wasm(root,cpp)
                self.assertEqual(file,again);self.assertFalse(first['cache_hit']);self.assertTrue(second['cache_hit'])
                file.write_bytes(b'corrupt');_,rebuilt=wasm.build_wasm(root,cpp);self.assertFalse(rebuilt['cache_hit'])
                with patch.object(wasm,'FLAGS',(*wasm.FLAGS,'-g0')):
                    changed,_=wasm.build_wasm(root,cpp);self.assertNotEqual(file,changed)
                version=wasm.subprocess.check_output([str(compiler),'--version'],env=env,timeout=10)
                with patch.object(wasm.subprocess,'check_output',return_value=version+b'fixture version delta'):
                    changed,_=wasm.build_wasm(root,cpp);self.assertNotEqual(file,changed)
                for path in (cpp,root/'scripts/wasm-platform.h',root/'scripts/wasm-product-host.cpp'):
                    path.write_bytes(path.read_bytes()+b'\n// identity change\n');changed,_=wasm.build_wasm(root,cpp);self.assertNotEqual(file,changed);file=changed


class BrowserBoundaryValidation(unittest.TestCase):
    def test_finish_never_turns_missing_uploads_into_another_prepare(self):
        with self.assertRaisesRegex(ValueError,'uploads'):detail.finish_browser([dict(compute_backend='browser_detail')],None)
    def test_browser_environment_requires_usable_toolchain(self):
        with patch.object(wasm,'availability',return_value=dict(available=True)):self.assertEqual(detail.execution_environment('browser'),{})
        with patch.object(wasm,'availability',return_value=dict(available=False,reason='missing emsdk')),self.assertRaisesRegex(detail.UnsupportedPortable,'emsdk'):detail.execution_environment('browser')
