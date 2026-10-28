"""Observe real argument objects once; never repair an invalid driver call."""
import copy,ctypes as C,json,struct,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_phase_audit import Journal,NativeLibrary,NativeFunction
from portable_partitioned_cuda_observer import observe
from portable_partitioned_cuda_trace import verify
from portable_partitioned_transport import plan,split
from portable_backend import READBACK_CHUNK_BYTES


class ObservedArgumentsTests(unittest.TestCase):
    def sequence(self,root,*,bad=None):
        layout=plan(struct.pack('<4I',3,11,22,33),1,1,2,runtime_stride=8)
        journal=Journal(root/'trace.jsonl');seen=[];index=0
        def allocation(pointer,size):
            nonlocal index
            C.cast(pointer,C.POINTER(C.c_uint64)).contents.value=[1000,2000,3000][index];index+=1;seen.append(('alloc',pointer,size));return 0
        def upload(*args):seen.append(('upload',*args));return 0
        def launch(*args):seen.append(('launch',*args));return 2 if bad=='native-failure' else 0
        driver=SimpleNamespace(cuMemAlloc_v2=allocation,cuMemcpyHtoD_v2=upload,cuLaunchKernel=launch)
        for name in ('cuInit','cuDeviceGet','cuDeviceComputeCapability','cuDeviceGetName','cuCtxCreate_v2','cuModuleLoadData','cuModuleGetFunction','cuModuleGetGlobal_v2','cuMemsetD8_v2','cuCtxSynchronize','cuMemcpyDtoH_v2','cuCtxDestroy_v2'):setattr(driver,name,lambda *a:0)
        lib=NativeLibrary(driver,journal)
        receipt=dict(enabled=True,hit=True,key='a'*64,artifact_sha256='b'*64,artifact_bytes=1,identity=dict(artifact='cubin'))
        journal.emit('cuda_compile_cache','verified',receipt=receipt)
        for name in ('cuInit','cuDeviceGet','cuDeviceComputeCapability','cuDeviceGetName','cuCtxCreate_v2','cuModuleLoadData','cuModuleGetFunction','cuModuleGetGlobal_v2'):getattr(lib,name)()
        transports=[]
        with observe(journal,layout):
            pointers=[]
            for i,size in enumerate((layout['maximum_input_buffer_bytes'],layout['maximum_output_buffer_bytes'],layout['maximum_runtime_buffer_bytes'])):
                pointer=C.c_uint64();arg=C.byref(pointer);pointers.append(arg)
                lib.cuMemAlloc_v2(arg,size+(4 if bad=='allocation' and i==1 else 0))
                self.assertIs(seen[-1][1],arg)
            for i,(batch,packed) in enumerate(zip(layout['batches'],split(struct.pack('<4I',3,11,22,33),layout),strict=True)):
                host=C.c_char_p(packed)
                lib.cuMemcpyHtoD_v2(1000,host,len(packed));self.assertIs(seen[-1][2],host)
                lib.cuMemsetD8_v2(2000,0,batch['output_bytes'])
                words=[1000,len(packed)//4,2000,batch['output_bytes']//4,3000,2]
                if bad=='parameters' and i==1:words[-1]=1
                params=C.create_string_buffer(struct.pack('<6Q',*words))
                lib.cuMemcpyHtoD_v2(5000,C.cast(params,C.c_void_p),48)
                count=batch['cases']+(1 if bad=='geometry' and i==1 else 0)
                result=lib.cuLaunchKernel(700,count,1,1,1,1,1,0,None,None,None)
                if result:raise RuntimeError('Original native failure '+str(result))
                lib.cuCtxSynchronize()
                journal.emit('cuda_readback_file','entered',device_address=2000,output_bytes=batch['output_bytes'],chunk_bytes=READBACK_CHUNK_BYTES)
                lib.cuMemcpyDtoH_v2(None,2000,batch['output_bytes'])
                stream=dict(output_bytes=batch['output_bytes'],output_sha256='c'*64,chunks=1,chunk_bytes=READBACK_CHUNK_BYTES)
                journal.emit('cuda_readback_file','returned',receipt=stream)
                transports.append(dict(backend='cuda',cases=batch['cases'],command_status='completed',compile_artifact=receipt,
                    input_bytes=batch['input_bytes'],output_bytes=batch['output_bytes'],readback_stream=stream,
                    runtime_stride_bytes=8,runtime_buffer_bytes=16,runtime_element_capacity=2))
        lib.cuCtxDestroy_v2()
        return [json.loads(s) for s in (root/'trace.jsonl').read_text().splitlines()],layout,transports,seen

    def test_original_argument_identity_and_exactly_one_forward_per_call(self):
        original=NativeFunction.__call__
        with tempfile.TemporaryDirectory() as temp:
            rows,layout,transports,seen=self.sequence(Path(temp))
            self.assertTrue(verify(rows,layout,transports,pid=rows[0]['pid'],require_arguments=True))
            self.assertEqual([s[0] for s in seen],['alloc']*3+['upload','upload','launch']*2)
        self.assertIs(NativeFunction.__call__,original)

    def test_wrong_sizes_abi_and_later_launch_rejected_and_observer_restored(self):
        original=NativeFunction.__call__
        for bad in ('allocation','parameters','geometry','native-failure'):
            with self.subTest(bad=bad),tempfile.TemporaryDirectory() as temp:
                with self.assertRaises((ValueError,RuntimeError)):self.sequence(Path(temp),bad=bad)
                rows=[json.loads(s) for s in (Path(temp)/'trace.jsonl').read_text().splitlines()]
                launches=[r for r in rows if r['stage']=='cuLaunchKernel' and r['state']=='entered']
                self.assertEqual(len(launches),0 if bad=='allocation' else 1)
            self.assertIs(NativeFunction.__call__,original)

    def test_missing_or_changed_actual_argument_receipts_cannot_pass_strict_protocol(self):
        with tempfile.TemporaryDirectory() as temp:
            original,layout,transports,_=self.sequence(Path(temp));pid=original[0]['pid']
            for kind in ('missing','grid','allocation','parameters','order','readback'):
                rows=copy.deepcopy(original)
                if kind=='missing':rows=[r for r in rows if not r['stage'].startswith('partitioned_')]
                elif kind=='grid':next(r for r in rows if r['stage']=='partitioned_cuda_launch')['grid'][0]+=1
                elif kind=='allocation':next(r for r in rows if r['stage']=='partitioned_cuda_allocation' and r['state']=='returned')['byte_count']+=4
                elif kind=='parameters':next(r for r in rows if r['stage']=='partitioned_cuda_upload' and r['slot']==1)['parameters'][-1]+=1
                elif kind=='order':rows[-2],rows[-1]=rows[-1],rows[-2]
                else:
                    for r in rows:
                        if r['stage']=='partitioned_cuda_allocation' and r.get('index')==1 and r['state']=='returned':r['device_address']=2500
                with self.subTest(kind=kind):self.assertFalse(verify(rows,layout,transports,pid=pid,require_arguments=True))

    def test_library_boundary_requires_the_existing_observer_and_blocks_nvrtc(self):
        layout=plan(struct.pack('<2I',1,0),1,1,1,runtime_stride=8)
        with tempfile.TemporaryDirectory() as temp:
            journal=Journal(Path(temp)/'phases.jsonl');calls=[]
            def unobserved(name):calls.append(name);return SimpleNamespace()
            with patch.object(C,'WinDLL',unobserved,create=True):
                with self.assertRaisesRegex(ValueError,'Only the cached'):
                    with observe(journal,layout):C.WinDLL('nvrtc.dll')
                self.assertEqual(calls,[])
                with self.assertRaisesRegex(ValueError,'original native API observer'):
                    with observe(journal,layout):C.WinDLL('nvcuda.dll')
                self.assertEqual(calls,['nvcuda.dll']);self.assertIs(C.WinDLL,unobserved)


if __name__=='__main__':unittest.main()
