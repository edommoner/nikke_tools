"""A successful first launch cannot conceal a failed or missing later batch."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import READBACK_CHUNK_BYTES as CHUNK
from portable_partitioned_cuda_trace import verify
from portable_phase_audit import verify_cuda_trace


def fixture(counts=(16,16,16,16,16,16,10)):
    rows=[];batches=[];transports=[];total=0
    receipt=dict(enabled=True,hit=True,key='a'*64,artifact_sha256='b'*64,artifact_bytes=1,identity=dict(artifact='cubin'))
    def emit(stage,state,**kw):rows.append(dict(stage=stage,state=state,pid=77,monotonic_ns=len(rows),**kw))
    def call(stage,**kw):emit(stage,'entered',**kw);emit(stage,'returned',return_code=0)
    emit('cuda_compile_cache','verified',receipt=receipt)
    for stage in ('cuInit','cuDeviceGet','cuDeviceComputeCapability','cuDeviceGetName','cuCtxCreate_v2','cuModuleLoadData','cuModuleGetFunction','cuModuleGetGlobal_v2',*(['cuMemAlloc_v2']*3)):call(stage)
    for n in counts:
        size=n*2064786*4;input_bytes=4+n*115680*4
        batches.append(dict(first_case=total,cases=n,input_bytes=input_bytes,output_bytes=size));total+=n
        call('cuMemcpyHtoD_v2');call('cuMemsetD8_v2',destination_device=1000,value=0,byte_count=size)
        call('cuMemcpyHtoD_v2');call('cuLaunchKernel');call('cuCtxSynchronize')
        emit('cuda_readback_file','entered',device_address=1000,output_bytes=size,chunk_bytes=CHUNK)
        chunks=(size+CHUNK-1)//CHUNK
        for i in range(chunks):call('cuMemcpyDtoH_v2',source_device=1000+i*CHUNK,byte_count=min(CHUNK,size-i*CHUNK))
        stream=dict(output_bytes=size,chunk_bytes=CHUNK,chunks=chunks,output_sha256='c'*64)
        emit('cuda_readback_file','returned',receipt=stream)
        transports.append(dict(backend='cuda',command_status='completed',cases=n,input_bytes=input_bytes,output_bytes=size,compile_artifact=receipt,readback_stream=stream))
    call('cuCtxDestroy_v2')
    return rows,dict(batches=batches,batch_size=16,input_count=total,output_words=2064786),transports


class SequenceTraceTests(unittest.TestCase):
    def test_all106_and_final_short_batch_with_single_context_cleanup(self):
        rows,layout,transports=fixture()
        self.assertTrue(verify(rows,layout,transports,pid=77))
        self.assertFalse(verify_cuda_trace(rows,pid=77))

    def test_single_batch_uses_explicit_protocol_too(self):
        self.assertTrue(verify(*fixture((10,)),pid=77))

    def test_later_failed_missing_or_extra_api_never_passes(self):
        for kind in ('failure','missing','extra','cleanup','raised'):
            rows,layout,transports=fixture()
            index=[i for i,r in enumerate(rows) if r['stage']=='cuLaunchKernel' and r['state']=='returned'][1]
            if kind=='failure':rows[index]['return_code']=2
            elif kind=='missing':del rows[index]
            elif kind=='extra':rows.insert(index,dict(rows[index],stage='cuUnexpected'))
            elif kind=='cleanup':rows[-1]['return_code']=1
            else:rows[index]['state']='raised'
            with self.subTest(kind=kind):self.assertFalse(verify(rows,layout,transports,pid=77))

    def test_stream_identity_offsets_zeros_receipts_and_complete_plan(self):
        for kind in ('offset','size','zeros','receipt','pointer','count','plan','last','hash'):
            rows,layout,transports=fixture()
            copies=[r for r in rows if r['stage']=='cuMemcpyDtoH_v2' and r['state']=='entered']
            requests=[r for r in rows if r['stage']=='cuda_readback_file' and r['state']=='entered']
            if kind=='offset':copies[-1]['source_device']+=1
            elif kind=='size':copies[-1]['byte_count']-=1
            elif kind=='zeros':next(r for r in rows if r['stage']=='cuMemsetD8_v2' and r['state']=='entered')['value']=1
            elif kind=='receipt':transports[-1]['readback_stream']=dict(transports[-1]['readback_stream'],chunks=1)
            elif kind=='pointer':requests[-1]['device_address']+=100
            elif kind=='count':transports[-1]['cases']-=1
            elif kind=='plan':layout['batches'][-1]['first_case']-=1
            elif kind=='last':layout['input_count']-=1
            else:transports[-1]['readback_stream']['output_sha256']='x'*64
            with self.subTest(kind=kind):self.assertFalse(verify(rows,layout,transports,pid=77))

    def test_cache_compile_pid_time_or_unknown_schema_is_not_success(self):
        for kind in ('compile','ptx','miss','pid','time','malformed','extra-cache'):
            rows,layout,transports=fixture()
            if kind=='compile':rows.append(dict(rows[-1],stage='nvrtcCompileProgram'))
            elif kind=='ptx':rows[0]['receipt']['identity']['artifact']='ptx'
            elif kind=='miss':rows[0]['receipt']['hit']=False
            elif kind=='pid':rows[-1]['pid']=88
            elif kind=='time':rows[-1]['monotonic_ns']=-1
            elif kind=='malformed':del rows[-1]['state']
            else:rows.append(dict(rows[0],monotonic_ns=len(rows)))
            with self.subTest(kind=kind):self.assertFalse(verify(rows,layout,transports,pid=77))


if __name__=='__main__':unittest.main()
