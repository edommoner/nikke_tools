"""Bounded file transport/trace fault injection; fake driver only, no real GPU."""
import contextlib,copy,ctypes as C,hashlib,importlib.util,json,os,struct,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_backend as backend
import portable_phase_audit as phase
import test_portable_resident_transport as fixture

class FileTransportTests(unittest.TestCase):
    def setUp(self):
        self.base=fixture.ResidentTransportTests();self.base.setUp();self.addCleanup(self.base.doCleanups)
        self.root=self.base.source.parent.resolve();self.path=self.root/'readback.partial';self.journal=phase.Journal(self.root/'phases.jsonl')
        self.base.driver.cuMemsetD8_v2=Mock(return_value=0);self.copies=[];self.fail_copy=None;self.compile_calls=0
        def copy(destination,source,size):
            offset=int(source)-0x20000;self.copies.append((offset,size))
            if self.fail_copy==len(self.copies):return 700
            pattern=bytes(range(251));start=offset%251
            data=(pattern*((size+start+250)//251))[start:start+size];C.memmove(destination,data,size)
            return 0
        self.base.driver.cuMemcpyDtoH_v2.side_effect=copy
        self.fake_os=types.SimpleNamespace(**dict(vars(os),name='nt',environ={'NIKKE_CUDA_ARTIFACT':'cubin'}))

    def run_cuda(self,size,paths=None,batches=None):
        def compile(*a,**k):
            self.compile_calls+=1
            self.journal.invoke('nvrtcCompileProgram',lambda:0,native=True)
            return b'\x7fELFfake',{}
        with patch.object(backend,'os',self.fake_os),patch.object(phase,'os',self.fake_os),patch.object(C,'WinDLL',return_value=self.base.driver,create=True),patch.object(backend,'compile_cuda_source',side_effect=compile) as compiler,phase.observe(backend,self.journal):
            result=backend.execute_cuda_batches(self.base.source,'portableEvents',batches or [struct.pack('<II',1,0)],[size],[1],resident=self.base.plan,output_paths=paths or [self.path])
        return result,compiler

    def rows(self):return [json.loads(line) for line in (self.root/'phases.jsonl').read_text().splitlines()]

    def test_all_bytes_offsets_tail_and_single_launch_with_one_bounded_buffer(self):
        size=2*backend.READBACK_CHUNK_BYTES+13;original=C.create_string_buffer;allocations=[]
        def allocate(n,*args):
            if isinstance(n,int):allocations.append(n);self.assertLessEqual(n,backend.READBACK_CHUNK_BYTES)
            return original(n,*args)
        with patch.object(C,'create_string_buffer',side_effect=allocate):(raw,metadata),compiler=self.run_cuda(size)
        self.assertEqual(raw,[None]);self.assertEqual(self.path.stat().st_size,size)
        self.assertEqual(self.copies,[(0,backend.READBACK_CHUNK_BYTES),(backend.READBACK_CHUNK_BYTES,backend.READBACK_CHUNK_BYTES),(2*backend.READBACK_CHUNK_BYTES,13)])
        expected=(bytes(range(251))*((size+250)//251))[:size]
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),hashlib.sha256(expected).hexdigest())
        self.assertEqual(metadata[0]['readback_stream'],dict(output_bytes=size,output_sha256=hashlib.sha256(expected).hexdigest(),chunk_bytes=backend.READBACK_CHUNK_BYTES,chunks=3))
        self.assertEqual(self.base.allocations,[8,size,16]);self.base.driver.cuLaunchKernel.assert_called_once();self.base.driver.cuCtxSynchronize.assert_called_once();self.base.driver.cuCtxDestroy_v2.assert_called_once()
        self.base.driver.cuMemsetD8_v2.assert_called_once();self.assertEqual(self.base.driver.cuMemsetD8_v2.call_args.args[1:],(0,size))
        self.assertEqual(self.base.driver.cuMemsetD8_v2.argtypes,[C.c_uint64,C.c_ubyte,C.c_size_t]);compiler.assert_called_once()
        self.assertEqual(allocations.count(backend.READBACK_CHUNK_BYTES),1);self.assertTrue(phase.verify_cuda_trace(self.rows(),pid=os.getpid()))

    def test_failed_second_chunk_preserves_only_prefix_and_cleans_context(self):
        self.fail_copy=2
        with self.assertRaisesRegex(RuntimeError,'CUDA error 700'):self.run_cuda(backend.READBACK_CHUNK_BYTES+7)
        self.assertEqual(self.path.stat().st_size,backend.READBACK_CHUNK_BYTES);self.assertEqual(len(self.copies),2)
        self.base.driver.cuCtxDestroy_v2.assert_called_once();self.assertFalse(phase.verify_cuda_trace(self.rows(),pid=os.getpid()))

    def test_zero_failure_stops_before_launch_or_readback(self):
        self.base.driver.cuMemsetD8_v2.return_value=700
        with self.assertRaisesRegex(RuntimeError,'cuMemsetD8'):self.run_cuda(32)
        self.base.driver.cuLaunchKernel.assert_not_called();self.assertFalse(self.copies);self.assertFalse(self.path.exists());self.base.driver.cuCtxDestroy_v2.assert_called_once()

    def test_existing_or_duplicate_file_is_rejected_before_compile_or_driver(self):
        self.path.write_bytes(b'original')
        with self.assertRaisesRegex(ValueError,'Fresh distinct'):self.run_cuda(32)
        self.assertEqual(self.path.read_bytes(),b'original');self.base.driver.cuInit.assert_not_called();self.assertEqual(self.compile_calls,0)
        with patch.object(backend,'os',self.fake_os),patch.object(backend,'compile_cuda_source') as compiler,self.assertRaisesRegex(ValueError,'Fresh distinct'):
            backend.execute_cuda_batches(self.base.source,'entry',[struct.pack('<I',1)]*2,[32]*2,[1]*2,output_paths=[self.root/'same']*2)
        compiler.assert_not_called()

    def test_short_file_write_keeps_failure_and_context_cleanup(self):
        original=Path.open;owner=self
        @contextlib.contextmanager
        def opened(path,*args,**kwargs):
            with original(path,*args,**kwargs) as stream:
                if path!=owner.path or args!=('xb',):yield stream;return
                class Short:
                    def write(self,view):return stream.write(view[:-1])
                yield Short()
        with patch.object(Path,'open',opened),self.assertRaisesRegex(OSError,'Short streamed'):
            self.run_cuda(32)
        self.assertEqual(self.path.stat().st_size,31);self.base.driver.cuCtxDestroy_v2.assert_called_once()
        self.assertFalse(phase.verify_cuda_trace(self.rows(),pid=os.getpid()))

    def test_context_cleanup_failure_cannot_keep_a_successful_trace(self):
        self.base.driver.cuCtxDestroy_v2.return_value=700
        with self.assertRaisesRegex(RuntimeError,'cuCtxDestroy'):self.run_cuda(32)
        self.assertEqual(self.path.stat().st_size,32);self.assertFalse(phase.verify_cuda_trace(self.rows(),pid=os.getpid()))

    def test_stream_trace_rejects_missing_failed_overlapping_or_unbounded_copies(self):
        self.run_cuda(backend.READBACK_CHUNK_BYTES+7);original=self.rows()
        for kind in ('missing','failed','offset','bytes','zero','receipt','chunk_bound','order'):
            rows=copy.deepcopy(original);copies=[r for r in rows if r['stage']=='cuMemcpyDtoH_v2'];markers=[r for r in rows if r['stage']=='cuda_readback_file']
            if kind=='missing':rows.remove(copies[-1])
            elif kind=='failed':copies[-1]['return_code']=700
            elif kind=='offset':copies[2]['source_device']-=1
            elif kind=='bytes':copies[2]['byte_count']+=1
            elif kind=='zero':next(r for r in rows if r['stage']=='cuMemsetD8_v2')['byte_count']-=1
            elif kind=='receipt':markers[-1]['receipt']['chunks']+=1
            elif kind=='chunk_bound':markers[0]['chunk_bytes']*=2
            elif kind=='order':copies[2]['monotonic_ns']=copies[0]['monotonic_ns']-1
            with self.subTest(kind=kind):self.assertFalse(phase.verify_cuda_trace(rows,pid=os.getpid()))

class FilePublicationTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve();(self.root/'research/portable-build').mkdir(parents=True)
        self.destination=self.root/'readback.bin';self.payload=struct.pack('<II',17,0xffffffff);self.hashes={'gpu/probe.slang':'source'}
        self.generated={k:self.root/('probe.'+k) for k in ('metal','cuda')}
        for p in self.generated.values():p.write_bytes(b'generated')
        self.transport=dict(backend='metal',cases=1,command_status='completed',input_bytes=8,output_bytes=8,file_readback_chunk_bytes=backend.READBACK_CHUNK_BYTES)
        self.build=Mock(return_value=(self.generated,self.hashes))
        self.mutate=None
    def metal(self,argv):
        Path(argv[4]).write_bytes(self.payload)
        if self.mutate:self.mutate()
        return types.SimpleNamespace(returncode=0,stdout=json.dumps(self.transport),stderr='')
    def execute(self,backendname='metal'):
        with patch.object(backend,'ROOT',self.root),patch.object(backend,'build',self.build) as build,patch.object(backend,'resident_plan',return_value=None),patch.object(backend,'source_hashes',side_effect=lambda *a:self.hashes),patch.object(backend,'run_metal_command',side_effect=self.metal),patch.object(backend.platform,'system',return_value='Darwin'):
            result=backend.execute('gpu/probe.slang','entry',struct.pack('<II',1,3),1,2,backendname,readback_path=self.destination)
        return result,build
    def test_common_file_route_preserves_exact_output_and_evidence_without_whole_read(self):
        original=Path.read_bytes
        def read(path):
            if path.name.startswith('readback'):raise AssertionError('Whole readback forbidden')
            return original(path)
        with patch.object(Path,'read_bytes',read):(raw,evidence),build=self.execute()
        self.assertIsNone(raw);self.assertEqual(self.destination.read_bytes(),self.payload);self.assertEqual(evidence['output_sha256'],hashlib.sha256(self.payload).hexdigest());self.assertTrue(evidence['gpu_execution_verified'])
        self.assertFalse(self.destination.with_name('readback.bin.partial').exists());build.assert_called_once()
    def test_existing_result_stops_before_build_and_preserves_bytes(self):
        self.destination.write_bytes(b'original')
        with patch.object(backend,'build') as build,self.assertRaisesRegex(ValueError,'Fresh readback'):self.execute()
        self.build.assert_not_called();self.assertEqual(self.destination.read_bytes(),b'original')
    def test_failed_metadata_keeps_partial_and_never_publishes(self):
        self.transport['command_status']='error'
        with self.assertRaisesRegex(RuntimeError,'Incomplete file'):self.execute()
        self.assertFalse(self.destination.exists());self.assertEqual(self.destination.with_name('readback.bin.partial').read_bytes(),self.payload)
    def test_racing_existing_final_cannot_be_overwritten(self):
        self.mutate=lambda:self.destination.write_bytes(b'other result')
        with self.assertRaises(FileExistsError):self.execute()
        self.assertEqual(self.destination.read_bytes(),b'other result');self.assertTrue(self.destination.with_name('readback.bin.partial').exists())

    def test_changed_source_never_publishes_a_success(self):
        original_hashes=self.hashes
        def change():self.hashes=dict(original_hashes,changed='source')
        self.mutate=change
        with self.assertRaisesRegex(RuntimeError,'source changed'):self.execute()
        self.assertFalse(self.destination.exists());self.assertTrue(self.destination.with_name('readback.bin.partial').exists())

    def test_broken_symlink_is_not_a_fresh_destination(self):
        try:self.destination.symlink_to(self.root/'absent')
        except OSError as error:
            if os.name=='nt' and getattr(error,'winerror',None)==1314:self.skipTest('Windows symlink creation privilege unavailable')
            raise
        with self.assertRaisesRegex(ValueError,'Fresh readback'):self.execute()
        self.build.assert_not_called();self.assertTrue(self.destination.is_symlink());self.assertFalse((self.root/'absent').exists())

    def test_cuda_common_file_bridge_binds_transport_receipt_and_destination(self):
        def cuda(source,entry,packed,size,count,*,output_path):
            self.assertEqual(output_path,self.destination.with_name('readback.bin.partial'));self.assertEqual((size,count),(8,1))
            output_path.write_bytes(self.payload)
            return None,dict(backend='cuda',cases=1,command_status='completed',input_bytes=8,output_bytes=8,readback_stream=dict(output_bytes=8,output_sha256=hashlib.sha256(self.payload).hexdigest(),chunk_bytes=backend.READBACK_CHUNK_BYTES,chunks=1))
        with patch.object(backend,'execute_cuda',side_effect=cuda) as run:(raw,evidence),_=self.execute('cuda')
        self.assertIsNone(raw);run.assert_called_once();self.assertEqual(evidence['backend'],'cuda');self.assertEqual(self.destination.read_bytes(),self.payload)

    def test_cuda_receipt_mismatch_keeps_partial_and_no_final(self):
        def cuda(*args,output_path,**kwargs):
            output_path.write_bytes(self.payload)
            return None,dict(backend='cuda',cases=1,command_status='completed',input_bytes=8,output_bytes=8,readback_stream=dict(output_bytes=8,output_sha256='0'*64,chunk_bytes=backend.READBACK_CHUNK_BYTES,chunks=1))
        with patch.object(backend,'execute_cuda',side_effect=cuda),self.assertRaisesRegex(RuntimeError,'digest mismatch'):self.execute('cuda')
        self.assertFalse(self.destination.exists());self.assertTrue(self.destination.with_name('readback.bin.partial').exists())

if __name__=='__main__':unittest.main()
