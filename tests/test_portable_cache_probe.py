"""Read-only cache inspection: synthetic artifacts, no NVIDIA libraries."""
import base64,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_backend as backend
from portable_compile_cache import get_or_compile,probe
s=importlib.util.spec_from_file_location('cache_probe_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)

class CacheProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.cuda=self.root/'cuda';(self.cuda/'bin').mkdir(parents=True)
        self.files=[self.cuda/'bin/nvrtc64_fixture.dll',self.cuda/'bin/nvrtc-builtins64_fixture.dll']
        for i,p in enumerate(self.files):p.write_bytes(('synthetic compiler'+str(i)).encode())
        self.source=self.root/'generated.cu';self.source.write_bytes(b'// synthetic generated source\n');self.cache=self.root/'cache'
    def seed(self,kind='cubin',level=None,payload=b'\x7fELF-synthetic-not-executable'):
        return get_or_compile(self.source.read_bytes(),backend.cuda_compile_options(kind,level),self.files,lambda:payload,self.cache,artifact_kind=kind)[1]
    def snapshot(self):return {p.name:p.read_bytes() for p in self.cache.iterdir()} if self.cache.exists() else {}
    def test_cold_probe_creates_no_directory_claim_or_compiler(self):
        receipt=backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda)
        self.assertFalse(receipt['hit']);self.assertTrue(receipt['probe_only']);self.assertFalse(self.cache.exists())
    def test_warm_probe_preserves_exact_legacy_key_bytes_and_cache(self):
        old=self.seed();before=self.snapshot()
        self.assertEqual(old['key'],'fad47743103832db04be68a070dc8b0fa7521b446dc3b70c599a42804d21506f')
        with patch.object(backend.C,'WinDLL',side_effect=AssertionError('NVRTC load'),create=True),patch.object(backend.C,'CDLL',side_effect=AssertionError('Native library')):
            r=backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda)
        self.assertTrue(r['hit']);self.assertEqual(r['key'],old['key']);self.assertEqual(r['identity'],old['identity']);self.assertEqual(r['artifact_sha256'],old['artifact_sha256']);self.assertEqual(self.snapshot(),before)
    def test_owned_or_abandoned_claim_is_reported_and_never_touched(self):
        r=backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda);self.cache.mkdir();claim=self.cache/(r['key']+'.claim');claim.write_bytes(b'unknown owner; not parseable')
        before=self.snapshot();r=backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda);self.assertFalse(r['hit']);self.assertTrue(r['claim_present']);self.assertEqual(self.snapshot(),before)
        _,seed=get_or_compile(self.source.read_bytes(),backend.cuda_compile_options('cubin'),self.files,lambda:b'\x7fELF-synthetic',self.root/'seed',artifact_kind='cubin')
        self.assertEqual(seed['key'],r['key']);(self.cache/(r['key']+'.json')).write_bytes((self.root/'seed'/(r['key']+'.json')).read_bytes())
        before=self.snapshot();self.assertTrue(backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda)['hit']);self.assertEqual(self.snapshot(),before)
    def test_exact_source_flags_and_compiler_changes_miss_without_publication(self):
        self.seed();before=self.snapshot()
        self.assertFalse(backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda,ptxas_level=1)['hit'])
        self.assertFalse(backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda,artifact_kind='ptx')['hit'])
        self.source.write_bytes(self.source.read_bytes()+b' ');self.assertFalse(backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda)['hit'])
        self.source.write_bytes(b'// synthetic generated source\n');self.files[0].write_bytes(b'changed compiler');self.assertFalse(backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda)['hit']);self.assertEqual(self.snapshot(),before)
    def test_header_bytes_participate_in_the_unchanged_cache_identity(self):
        header=self.root/'prelude.h';header.write_bytes(b'header-v1');raw=('#include "'+header.as_posix()+'"\n').encode();self.source.write_bytes(raw)
        from portable_compile_cache import quoted_headers
        get_or_compile(raw,backend.cuda_compile_options('ptx'),self.files,lambda:b'synthetic PTX',self.cache,header_files=quoted_headers(raw))
        self.assertTrue(backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda,artifact_kind='ptx')['hit']);before=self.snapshot();header.write_bytes(b'header-v2');self.assertFalse(backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda,artifact_kind='ptx')['hit']);self.assertEqual(self.snapshot(),before)
    def test_corrupt_and_empty_artifacts_fail_closed_and_remain_unchanged(self):
        r=self.seed();path=self.cache/(r['key']+'.json');original=path.read_bytes()
        for change in ('hash','base64','empty','identity'):
            x=json.loads(original)
            if change=='hash':x['artifact_sha256']='0'*64
            if change=='base64':x['artifact_base64']='***'
            if change=='identity':x['identity']['source_sha256']='0'*64
            if change=='empty':x.update(artifact_base64='',artifact_bytes=0,artifact_sha256=hashlib.sha256(b'').hexdigest())
            path.write_text(json.dumps(x));before=self.snapshot()
            with self.subTest(change=change),self.assertRaises(ValueError):backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda)
            self.assertEqual(self.snapshot(),before)
    def test_cubin_format_and_ambiguous_toolchains_are_rejected(self):
        self.seed(payload=b'synthetic invalid ELF')
        with self.assertRaisesRegex(RuntimeError,'ELF'):backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda)
        (self.cuda/'bin/nvrtc64_another.dll').write_bytes(b'other')
        with self.assertRaisesRegex(RuntimeError,'exactly one'):backend.probe_cuda_source_cache(self.source,self.cache,cuda_root=self.cuda)
    def test_cli_miss_hit_require_hit_and_report_are_read_only(self):
        interpreter=getattr(sys,'_base_executable',sys.executable) if sys.platform=='win32' else sys.executable
        def run(label,required=False):
            out=self.root/(label+'.json');args=[interpreter,str(ROOT/'scripts/nikke_gpu.py'),'cache-probe','--generated-cuda',str(self.source),'--cuda-root',str(self.cuda),'--compile-cache',str(self.cache),'--out',str(out)]
            if required:args.append('--require-hit')
            p=subprocess.run(args,capture_output=True,text=True,timeout=10);return p,json.loads(out.read_text())
        p,r=run('cold');self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(r['cache']['hit']);self.assertFalse(self.cache.exists());self.assertFalse(r['calculation_verified'])
        p,r=run('cold-required',True);self.assertEqual(p.returncode,1);self.assertFalse(self.cache.exists())
        self.seed();before=self.snapshot();p,r=run('warm',True);self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(r['cache']['hit']);self.assertEqual(self.snapshot(),before)
    def test_cli_report_never_overwrites_or_writes_inside_cache_toolchain(self):
        out=self.root/'report.json';out.write_bytes(b'preserved')
        with self.assertRaises(FileExistsError):cli.cache_probe(self.source,self.cuda,self.cache,out)
        self.assertEqual(out.read_bytes(),b'preserved')
        for folder in (self.cuda,self.cache):
            with self.assertRaisesRegex(ValueError,'outside'):cli.cache_probe(self.source,self.cuda,self.cache,folder/'report.json')

if __name__=='__main__':unittest.main()
