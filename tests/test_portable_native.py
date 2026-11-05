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


class NativeSourceHistoryTests(unittest.TestCase):
    """Reviewed native bytes invert exactly; additional edits stay unreviewed."""
    def rows(self):
        return json.loads((ROOT/'tests/fixtures/portable-native-backend-source-delta.json').read_text())['files']

    def test_exact_native_inverse_recovers_all_three_previous_file_digests(self):
        from portable_native_backend_source_contract import native_preimage
        expected={
            'app/portable_slang_generation.py':'a3285cc9b372e4bb592fd70fdc18e44b07b6803a2c432eca8a8f0493eae76dac',
            'app/portable_backend.py':'ad1f55129422b4b80e34bd21f41cdb045f2d1a0d9f0a201e0c6c2e8be8c5b08e',
        }
        rows=self.rows();self.assertEqual(set(rows),{'app/portable_slang_generation.py','app/portable_detail.py','app/portable_backend.py'})
        for name,row in rows.items():
            from portable_removed_sources import REMOVED_SOURCES
            if name in REMOVED_SOURCES:continue
            with self.subTest(name=name):
                raw=(ROOT/name).read_bytes()
                from portable_browser_backend_source_contract import reviewed_bytes as browser_reviewed_bytes
                from portable_optimizer_six_source_contract import reviewed_bytes as six_reviewed_bytes
                reviewed=browser_reviewed_bytes(ROOT,name,six_reviewed_bytes(ROOT,name,raw))
                self.assertEqual(hashlib.sha256(reviewed).hexdigest(),row['after_sha256'])
                previous=native_preimage(ROOT,name,raw)
                self.assertEqual(hashlib.sha256(previous).hexdigest(),row['before_sha256'])
                if name in expected:self.assertEqual(row['before_sha256'],expected[name])
                self.assertEqual(native_preimage(ROOT,name,previous),previous)

    def test_one_byte_extra_edit_is_rejected_for_each_reviewed_file(self):
        from portable_native_backend_source_contract import native_preimage,reviewed_bytes
        for name in self.rows():
            from portable_removed_sources import REMOVED_SOURCES
            if name in REMOVED_SOURCES:continue
            raw=(ROOT/name).read_bytes()
            for changed in (raw+b'\n',b'!'+raw[1:],raw[:-1]):
                with self.subTest(name=name,delta=len(changed)-len(raw)),self.assertRaisesRegex(ValueError,'Unreviewed native backend source'):
                    native_preimage(ROOT,name,changed)
                self.assertEqual(reviewed_bytes(ROOT,name,changed),changed)

    def test_existing_historical_guards_still_reject_extra_byte(self):
        from portable_generation_extraction_source_contract import project_generation_source
        from portable_metal_deadline_source_contract import historical_backend_bytes
        from portable_arena_transport_source_contract import historical_backend_source
        import portable_weighted_incoming_source_contract as weighted
        with self.assertRaisesRegex(ValueError,'Unreviewed'):
            project_generation_source(ROOT,(ROOT/'app/portable_slang_generation.py').read_text()+'\n')
        changed=(ROOT/'app/portable_backend.py').read_bytes()+b'\n'
        with self.assertRaisesRegex(ValueError,'Unreviewed'):historical_backend_bytes(ROOT,changed)
        with self.assertRaises(ValueError):historical_backend_source(ROOT,changed.decode())
        original=Path.read_bytes;detail_path=ROOT/'app/portable_detail.py'
        def read(path):
            raw=original(path)
            return raw+b'\n' if path==detail_path else raw
        with patch.object(Path,'read_bytes',read),self.assertRaisesRegex(ValueError,'Unreviewed product source: app/portable_detail.py'):
            weighted.boss_source_preimages(ROOT)

    def test_prior_generation_guard_history_is_exact_and_rejects_extra_byte(self):
        from portable_native_backend_source_contract import native_preimage
        from portable_generation_extraction_source_contract import output_guards_preimage,project_generation_source
        name='app/portable_slang_generation.py'
        previous=native_preimage(ROOT,name,(ROOT/name).read_bytes()).decode()
        restored=output_guards_preimage(ROOT,previous)
        self.assertEqual(hashlib.sha256(restored.encode()).hexdigest(),'adbcf4d480069b0b3e35493624d6d6c4422d57c76fa2b4a3b16257b72796e6b8')
        self.assertEqual(project_generation_source(ROOT,previous),project_generation_source(ROOT))
        with self.assertRaisesRegex(ValueError,'Unreviewed'):project_generation_source(ROOT,previous+'\n')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'tests/fixtures';path.mkdir(parents=True)
            ledger='portable-generation-output-guards-source-delta.json'
            (path/ledger).write_bytes((ROOT/'tests/fixtures'/ledger).read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'Generation output guards ledger changed'):
                output_guards_preimage(root,previous)

    def test_native_ledger_edit_is_rejected(self):
        from portable_native_backend_source_contract import native_preimage
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'tests/fixtures';path.mkdir(parents=True)
            (path/'portable-native-backend-source-delta.json').write_bytes((ROOT/'tests/fixtures/portable-native-backend-source-delta.json').read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'Native backend source ledger changed'):
                native_preimage(root,'app/portable_backend.py',__import__('portable_optimizer_six_source_contract').reviewed_bytes(ROOT,'app/portable_backend.py',(ROOT/'app/portable_backend.py').read_bytes()))

    def test_inverse_checks_span_and_reconstructed_digest(self):
        import portable_native_backend_source_contract as history
        name='app/portable_backend.py';raw=__import__('portable_optimizer_six_source_contract').reviewed_bytes(ROOT,name,(ROOT/name).read_bytes())
        data=json.loads((ROOT/'tests/fixtures/portable-native-backend-source-delta.json').read_text())
        for key,value,error in [('after','wrong span','inverse span changed'),('before','wrong previous bytes','historical preimage changed')]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as folder:
                changed=copy.deepcopy(data);changed['files'][name]['hunks'][0][key]=value
                ledger=(json.dumps(changed,indent=2)+'\n').encode()
                root=Path(folder);path=root/'tests/fixtures';path.mkdir(parents=True)
                (path/'portable-native-backend-source-delta.json').write_bytes(ledger)
                with patch.object(history,'LEDGER_SHA256',hashlib.sha256(ledger).hexdigest()),self.assertRaisesRegex(ValueError,error):
                    history.native_preimage(root,name,raw)


if __name__=='__main__':unittest.main()
