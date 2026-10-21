import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_compile_cache import get_or_compile
from portable_phase_audit import verify_cuda_trace

class CompileCacheTests(unittest.TestCase):
    def test_hit_requires_exact_source_flags_and_compiler_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);dll=root/'nvrtc.dll';dll.write_bytes(b'compiler')
            compile=Mock(return_value=b'ptx\0')
            def run(source=b'cuda',options=['--fmad=false']):
                return get_or_compile(source,options,[dll],compile,root/'cache')
            a,first=run();b,second=run();self.assertFalse(first['hit']);self.assertTrue(second['hit'])
            self.assertEqual(a,b);self.assertEqual(compile.call_count,1)
            run(source=b'cuda ');run(options=['--fmad=true']);dll.write_bytes(b'compiler2');run()
            self.assertEqual(compile.call_count,4)

    def test_corruption_fails_closed_without_compile_or_replacing_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);dll=root/'nvrtc.dll';dll.write_bytes(b'compiler')
            compile=Mock(return_value=b'ptx')
            _,receipt=get_or_compile(b'cuda',[],[dll],compile,root/'cache')
            path=root/'cache'/(receipt['key']+'.json');value=json.loads(path.read_text())
            value['artifact_base64']='YmFk';path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'integrity'):
                get_or_compile(b'cuda',[],[dll],compile,root/'cache')
            self.assertEqual(compile.call_count,1)

    def test_disabled_cache_always_compiles(self):
        compile=Mock(return_value=b'ptx')
        for _ in range(2):self.assertFalse(get_or_compile(b'cuda',[],[],compile)[1]['enabled'])
        self.assertEqual(compile.call_count,2)

    def test_cache_hit_trace_still_requires_successful_ordered_launch_and_readback(self):
        receipt=dict(enabled=True,hit=True,key='a'*64,artifact_sha256='b'*64,artifact_bytes=3)
        rows=[dict(stage='cuda_compile_cache',state='verified',receipt=receipt,monotonic_ns=0,pid=1)]
        for stage in ('cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2'):
            rows.extend([dict(stage=stage,state='entered',monotonic_ns=len(rows),pid=1),
                         dict(stage=stage,state='returned',return_code=0,monotonic_ns=len(rows)+1,pid=1)])
        self.assertTrue(verify_cuda_trace(rows,pid=1))
        self.assertFalse(verify_cuda_trace(rows[1:],pid=1))
        self.assertFalse(verify_cuda_trace(rows[:-1],pid=1))
        receipt['hit']=False;self.assertFalse(verify_cuda_trace(rows,pid=1))


class CacheCheckCLITests(unittest.TestCase):
    def test_warm_check_never_compiles_and_rejects_changed_compiler(self):
        import importlib.util,os
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('cache_check_cli',ROOT/'scripts/nikke_gpu.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);capture=root/'capture';capture.mkdir()
            cuda=root/'cuda';(cuda/'bin').mkdir(parents=True);dll=cuda/'bin/nvrtc.dll';dll.write_bytes(b'compiler')
            cache=root/'cache';source=b'generated';options=['--fmad=false']
            artifact,receipt=get_or_compile(source,options,[dll],lambda:b'ptx',cache)
            (capture/'generated.cu').write_bytes(source);(capture/'compiled.ptx').write_bytes(artifact)
            cli.write(capture/'run.json',dict(package_id='fixture',backend='cuda'))
            cli.write(capture/'evidence.json',dict(backend='cuda',transport=dict(compile_artifact=receipt)))
            records=cli.file_records(capture,['generated.cu','compiled.ptx','run.json','evidence.json'])
            cli.write(capture/'artifacts.json',dict(files=records))
            with patch.object(cli,'verify_package',return_value=dict(package_id='fixture',backend='cuda')),patch.dict(os.environ,{'CUDA_PATH':str(cuda),'NIKKE_CUDA_COMPILE_CACHE':str(cache)}):
                report=cli.check_compile_cache(capture,root/'warm.json')
                self.assertTrue(report['passed']);self.assertEqual(report['gpu_calls'],0)
                self.assertEqual(report['nvrtc_compile_calls'],0)
                dll.write_bytes(b'changed')
                with self.assertRaisesRegex(RuntimeError,'compilation forbidden'):
                    cli.check_compile_cache(capture,root/'miss.json')
                self.assertFalse((root/'miss.json').exists())


class HeaderIdentityTests(unittest.TestCase):
    def test_nested_quoted_headers_are_relative_and_change_the_key(self):
        from portable_compile_cache import quoted_headers
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'nested.h').write_text('first')
            prelude=root/'prelude.h';prelude.write_text('#include "nested.h"\n')
            source=('#include "'+str(prelude)+'"\n').encode()
            headers=quoted_headers(source)
            self.assertEqual(set(headers),{prelude.resolve(),(root/'nested.h').resolve()})
            _,a=get_or_compile(source,[],[],lambda:b'ptx',header_files=headers)
            (root/'nested.h').write_text('second')
            _,b=get_or_compile(source,[],[],lambda:b'ptx',header_files=quoted_headers(source))
            self.assertNotEqual(a['key'],b['key'])


class FailedModuleCaptureTests(unittest.TestCase):
    def test_successful_compiler_artifact_can_be_checked_after_module_timeout(self):
        import importlib.util,os
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('failed_cache_cli',ROOT/'scripts/nikke_gpu.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);capture=root/'capture';capture.mkdir()
            cuda=root/'cuda';(cuda/'bin').mkdir(parents=True);dll=cuda/'bin/nvrtc.dll';dll.write_bytes(b'compiler')
            cache=root/'cache';source=b'generated'
            artifact,receipt=get_or_compile(source,[],[dll],lambda:b'cubin',cache,artifact_kind='cubin')
            (capture/'generated.cu').write_bytes(source);(capture/'compiled.cubin').write_bytes(artifact)
            cli.write(capture/'run.json',dict(package_id='fixture',backend='cuda'))
            line=json.dumps(dict(stage='cuda_compile_cache',state='verified',receipt=receipt))+'\n'
            (capture/'phases.jsonl').write_text(line)
            names=['generated.cu','compiled.cubin','run.json','phases.jsonl']
            cli.write(capture/'artifacts.json',dict(files=cli.file_records(capture,names)))
            with patch.object(cli,'verify_package',return_value=dict(package_id='fixture')),patch.dict(os.environ,{'CUDA_PATH':str(cuda),'NIKKE_CUDA_COMPILE_CACHE':str(cache)}):
                report=cli.check_compile_cache(capture,root/'warm.json')
                self.assertTrue(report['passed']);self.assertFalse(report['calculation_verified'])
                self.assertEqual(report['gpu_calls'],0);self.assertEqual(report['nvrtc_compile_calls'],0)
                (capture/'phases.jsonl').write_text('{\n'+line)
                cli.write(capture/'artifacts.json',dict(files=cli.file_records(capture,names)))
                with self.assertRaises(json.JSONDecodeError):cli.check_compile_cache(capture,root/'bad.json')
                self.assertFalse((root/'bad.json').exists())

if __name__=='__main__':unittest.main()
