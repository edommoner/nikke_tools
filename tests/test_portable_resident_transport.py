"""CPU driver doubles validate 48-byte resident ABI and fail-before-launch gates."""
import ctypes as C,os,struct,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_backend as backend
from portable_resident_layout import cuda_layout_assertions


class ResidentTransportTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.source=Path(self.temporary.name)/'probe.cu';self.plan=dict(stride=16,alignment=8)
        self.source.write_bytes(cuda_layout_assertions(b'struct Runtime_0\n{ uint small; ulonglong big; };\n',self.plan))
        names=('cuInit','cuDeviceGet','cuDeviceGetName','cuDeviceComputeCapability','cuCtxCreate_v2','cuCtxDestroy_v2','cuModuleLoadData','cuModuleGetFunction','cuModuleGetGlobal_v2','cuMemAlloc_v2','cuMemcpyHtoD_v2','cuMemcpyDtoH_v2','cuCtxSynchronize','cuLaunchKernel')
        self.driver=types.SimpleNamespace(**{name:Mock(return_value=0) for name in names})
        def put(pointer,ty,value):C.cast(pointer,C.POINTER(ty))[0]=ty(value)
        def context(pointer,*args):put(pointer,C.c_void_p,1);return 0
        def capability(major,minor,*args):put(major,C.c_int,8);put(minor,C.c_int,6);return 0
        self.driver.cuCtxCreate_v2.side_effect=context;self.driver.cuDeviceComputeCapability.side_effect=capability
        self.allocations=[]
        def allocate(pointer,size):self.allocations.append(size);put(pointer,C.c_uint64,0x10000*len(self.allocations));return 0
        self.driver.cuMemAlloc_v2.side_effect=allocate
        self.global_size=48
        def global_symbol(pointer,size,*args):put(pointer,C.c_uint64,0xdead);put(size,C.c_size_t,self.global_size);return 0
        self.driver.cuModuleGetGlobal_v2.side_effect=global_symbol
        self.parameters=[]
        def copy(destination,source,size):
            if getattr(destination,'value',destination)==0xdead:self.parameters.append(struct.unpack('<QQQQQQ',C.string_at(source,size)))
            return 0
        self.driver.cuMemcpyHtoD_v2.side_effect=copy

    def execute(self,plan=None):
        fake_os=types.SimpleNamespace(name='nt',environ={'NIKKE_CUDA_ARTIFACT':'cubin'})
        with patch.object(backend,'os',fake_os),patch.object(backend,'compile_cuda_source',return_value=(b'\x7fELFfake',{})) as compiler,patch.object(C,'WinDLL',return_value=self.driver,create=True) as loader:
            result=backend.execute_cuda_batches(self.source,'portableEvents',[struct.pack('<II',1,0),struct.pack('<III',2,0,0)],[32,64],[1,2],resident=self.plan if plan is None else plan)
        return result,compiler,loader

    def test_gpu_buffer_capacity_is_maximum_batch_and_every_parameter_block_is_48_bytes(self):
        (raw,transports),compiler,loader=self.execute()
        self.assertEqual([len(b) for b in raw],[32,64]);self.assertEqual(self.allocations,[12,64,32])
        self.assertEqual(len(self.parameters),2)
        self.assertTrue(all(row[-2:]==(0x30000,2) for row in self.parameters))
        self.assertEqual([c.args[1] for c in self.driver.cuLaunchKernel.call_args_list],[1,2])
        self.assertTrue(all(t['runtime_stride_bytes']==16 and t['runtime_buffer_bytes']==32 and t['runtime_element_capacity']==2 for t in transports))
        loader.assert_called_once_with('nvcuda.dll');compiler.assert_called_once();self.driver.cuCtxDestroy_v2.assert_called_once()

    def test_wrong_constant_buffer_size_stops_before_launch_and_cleans_context(self):
        self.global_size=32
        with self.assertRaisesRegex(RuntimeError,'constant buffer ABI'):self.execute()
        self.driver.cuLaunchKernel.assert_not_called();self.driver.cuCtxDestroy_v2.assert_called_once()

    def test_host_stride_must_agree_with_compiler_assertions_before_dll_or_compile(self):
        with self.assertRaisesRegex(ValueError,'allocation disagrees'):self.execute(dict(self.plan,stride=8))
        self.assertEqual(self.allocations,[]);self.driver.cuInit.assert_not_called()


if __name__=='__main__':unittest.main()
