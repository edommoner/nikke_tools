"""Native transport tests use a small ABI fixture, never claim GPU parity."""
import copy,hashlib,json,os,struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_backend as backend
import portable_detail as detail
import portable_native as native
import portable_slang_generation as generation

FIXTURE='''#include <cstdint>
#include <cstddef>
struct Runtime_0 { uint32_t state; };
template<class T> struct Buffer { T* data; size_t count; };
struct GlobalParams_0 { Buffer<uint32_t> in,out; Buffer<Runtime_0> runtime; };
struct ComputeThreadVaryingInput { uint32_t index=0; };
void portableEvents_Thread(ComputeThreadVaryingInput* v,void*,GlobalParams_0* p) {
 p->out.data[0]=p->in.data[0];p->out.data[1]=p->in.data[1]+p->runtime.data[0].state++;
 p->out.data[2]=v->index;
}
'''

class NativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'research/portable-build').mkdir(parents=True)
        (self.root/'scripts').mkdir();(self.root/'scripts/native-product-host.cpp').write_bytes((ROOT/'scripts/native-product-host.cpp').read_bytes())
        self.cpp=self.root/'kernel.cpp';self.cpp.write_text(FIXTURE)

    def test_host_build_cache_parallel_isolation_and_invalid_input(self):
        host,first=native.build_host(self.root,self.cpp);again,second=native.build_host(self.root,self.cpp)
        self.assertEqual(host,again);self.assertFalse(first['cache_hit']);self.assertTrue(second['cache_hit'])
        inp=self.root/'input';out=self.root/'out';inp.write_bytes(struct.pack('<5I',4,10,20,30,40))
        status=native.run_host(host,inp,out,1,4,4,10)
        self.assertEqual(struct.unpack('<16I',out.read_bytes()),(1,10,0,0,1,20,0,0,1,30,0,0,1,40,0,0))
        self.assertTrue(status['device'].startswith('cpu:'));self.assertEqual(status['threads'],min(4,os.cpu_count() or 1))
        self.cpp.write_text(FIXTURE+'\n// identity change\n');changed,_=native.build_host(self.root,self.cpp);self.assertNotEqual(host,changed)
        inp.write_bytes(struct.pack('<2I',2,10))
        with self.assertRaisesRegex(RuntimeError,'wire dimensions'):native.run_host(host,inp,out,1,4,2,10)

    def execute(self,path=None,hashes=None):
        packed=struct.pack('<3I',2,11,22)
        with patch.object(backend,'ROOT',self.root),patch.object(backend,'build',return_value=({'cpp':self.cpp},{'source':'hash'})) as build,patch.object(backend,'source_hashes',return_value=hashes or {'source':'hash'}),patch.object(backend,'validate_composed_stride'):
            result=backend.execute('gpu/product_battle_entry.slang','portableEvents',packed,1,4,'native',readback_path=path)
        build.assert_called_once_with('gpu/product_battle_entry.slang','portableEvents',target='cpp')
        return result

    def test_backend_file_and_memory_readback_and_no_gpu_evidence(self):
        path=self.root/'readback.bin';raw,evidence=self.execute(path)
        self.assertIsNone(raw);self.assertEqual(path.stat().st_size,32);self.assertFalse(path.with_suffix('.bin.partial').exists())
        self.assertEqual(evidence['output_sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertTrue(evidence['native_execution_verified']);self.assertFalse(evidence['gpu_execution_verified'])
        detail.verified_transport(evidence,'native',cases=2)
        raw,again=self.execute();self.assertEqual(raw,path.read_bytes());self.assertEqual(evidence['output_sha256'],again['output_sha256'])
        with self.assertRaisesRegex(ValueError,'Fresh readback'):self.execute(path)

    def test_source_change_prevents_publication_preserves_partial(self):
        path=self.root/'readback.bin'
        with self.assertRaisesRegex(RuntimeError,'source changed'):self.execute(path,{'source':'different'})
        self.assertFalse(path.exists());self.assertTrue(path.with_suffix('.bin.partial').exists())

    def test_transport_requires_native_verification_and_valid_timing(self):
        _,evidence=self.execute()
        for field,value in [('native_execution_verified',False),('gpu_execution_verified',True)]:
            bad=copy.deepcopy(evidence);bad[field]=value
            with self.assertRaises(RuntimeError):detail.verified_transport(bad,'native',cases=2)
        for value in (float('nan'),float('inf'),-1,True):
            bad=copy.deepcopy(evidence);bad['transport']['host_seconds']=value
            with self.assertRaises(RuntimeError):detail.verified_transport(bad,'native',cases=2)
        with self.assertRaises(ValueError):backend.execute('x','portableEvents',b'',1,4,'native')

    def test_environment_and_batch_limits(self):
        self.assertEqual(detail.batch_limit([{'compute_backend':'native_detail'}]*32),32)
        self.assertEqual(detail.batch_limit([{'compute_backend':'metal_detail'}]*8),8)
        self.assertEqual(detail.batch_limit([{'compute_backend':'cuda_shared_detail'}]*8),8)
        with patch.object(native,'availability',return_value={'available':True}):self.assertEqual(detail.execution_environment('native'),{})
        with patch.object(native,'availability',return_value={'available':False,'reason':'slangcが必要です。'}),self.assertRaisesRegex(detail.UnsupportedPortable,'slangc'):detail.execution_environment('native')

    def test_cpp_generation_flags_and_source_guard(self):
        import subprocess
        (self.root/'gpu').mkdir();(self.root/'gpu/product.slang').write_text('// fixture')
        def compiler(command,**kw):
            self.assertEqual(command[2:],['-entry','portableEvents','-target','cpp','-fp-mode','precise','-line-directive-mode','none'])
            return subprocess.CompletedProcess(command,0,b'// generated',b'')
        with patch.object(generation,'cpp_compiler_identity',return_value={'fixture':True}),patch.object(generation.subprocess,'run',side_effect=compiler):
            outputs,hashes=generation.build(self.root,'gpu/product.slang','portableEvents',target='cpp')
        self.assertEqual(set(outputs),{'cpp'});self.assertEqual(hashes,generation.source_hashes(self.root,'gpu/product.slang'))
        def changed(command,**kw):
            (self.root/'gpu/product.slang').write_text('// changed');return compiler(command,**kw)
        with patch.object(generation,'cpp_compiler_identity',return_value={'fixture':'changed'}),patch.object(generation.subprocess,'run',side_effect=changed),self.assertRaisesRegex(RuntimeError,'sources changed'):
            generation.build(self.root,'gpu/product.slang','portableEvents',target='cpp')


if __name__=='__main__':unittest.main()
