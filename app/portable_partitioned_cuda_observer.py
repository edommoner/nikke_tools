"""Observe and bind real sequence arguments without changing the driver calls.

Nested inside portable_phase_audit.observe. No compiler, driver load or query is
introduced here. Validate the existing adapter's allocations, ABI uploads and
launch geometry, then forward the identical argument objects exactly once.
"""
import contextlib,ctypes as C,struct
from unittest.mock import patch


def integer(value):return int(getattr(value,'value',value))


@contextlib.contextmanager
def observe(journal,layout):
    from portable_phase_audit import NativeFunction,NativeLibrary
    batches=layout['batches'];count=len(batches)
    if (not count or layout.get('runtime_stride_bytes',0)<=0
        or sum(b['cases'] for b in batches)!=layout['input_count']):raise ValueError('Complete resident partition plan required')
    sizes=[layout['maximum_input_buffer_bytes'],layout['maximum_output_buffer_bytes'],layout['maximum_runtime_buffer_bytes']]
    allocation=[];uploads=0;launches=0;function=None
    original=NativeFunction.__call__

    def checked(self,*args):
        nonlocal uploads,launches,function
        stage=self._name
        if stage=='cuMemAlloc_v2':
            i=len(allocation)
            if i>=3 or len(args)!=2 or integer(args[1])!=sizes[i]:raise ValueError('CUDA sequence allocation differs from bounded plan')
            journal.emit('partitioned_cuda_allocation','entered',index=i,byte_count=sizes[i])
            result=original(self,*args)
            if integer(result)==0:
                address=C.cast(args[0],C.POINTER(C.c_uint64)).contents.value
                if not 0<address<2**64-sizes[i] or any(not (address+sizes[i]<=a or a+s<=address) for a,s in allocation):
                    raise ValueError('CUDA sequence allocation address is invalid or overlaps')
                allocation.append((address,sizes[i]))
                journal.emit('partitioned_cuda_allocation','returned',index=i,byte_count=sizes[i],device_address=address,return_code=0)
            else:journal.emit('partitioned_cuda_allocation','returned',index=i,byte_count=sizes[i],return_code=integer(result))
            return result
        if stage=='cuMemcpyHtoD_v2':
            batch=uploads//2;slot=uploads%2
            if len(allocation)!=3 or batch>=count or len(args)!=3:raise ValueError('Unexpected CUDA sequence upload')
            b=batches[batch];destination=integer(args[0]);size=integer(args[2])
            if slot==0:
                if destination!=allocation[0][0] or size!=b['input_bytes']:raise ValueError('CUDA sequence input upload differs')
                facts=dict(batch=batch,slot=slot,destination_device=destination,byte_count=size)
            else:
                if size!=48:raise ValueError('CUDA sequence constant ABI upload differs')
                params=list(struct.unpack('<6Q',C.string_at(args[1],48)))
                expected=[allocation[0][0],b['input_bytes']//4,allocation[1][0],b['output_bytes']//4,allocation[2][0],max(b['cases'] for b in batches)]
                if params!=expected:raise ValueError('CUDA sequence buffer/stride parameters differ')
                facts=dict(batch=batch,slot=slot,destination_device=destination,byte_count=size,parameters=params)
            journal.emit('partitioned_cuda_upload','entered',**facts)
            result=original(self,*args)
            journal.emit('partitioned_cuda_upload','returned',**facts,return_code=integer(result))
            if integer(result)==0:uploads+=1
            return result
        if stage=='cuLaunchKernel':
            if len(allocation)!=3 or launches>=count or uploads!=2*(launches+1) or len(args)!=11:
                raise ValueError('CUDA sequence launch lacks its own uploads')
            grid=list(map(integer,args[1:4]));block=list(map(integer,args[4:7]));shared=integer(args[7]);handle=integer(args[0])
            if (grid!=[batches[launches]['cases'],1,1] or block!=[1,1,1] or shared!=0
                or any(a is not None and integer(a)!=0 for a in args[8:]) or not handle
                or function is not None and function!=handle):raise ValueError('CUDA sequence native launch geometry differs')
            function=handle;facts=dict(batch=launches,function=handle,grid=grid,block=block,shared_bytes=shared,default_stream=True,null_kernel_parameters=True)
            journal.emit('partitioned_cuda_launch','entered',**facts)
            result=original(self,*args)
            journal.emit('partitioned_cuda_launch','returned',**facts,return_code=integer(result))
            if integer(result)==0:launches+=1
            return result
        return original(self,*args)

    loader=getattr(C,'WinDLL',None)
    def library(name,*args,**kwargs):
        if str(name).replace('\\','/').rsplit('/',1)[-1].lower()!='nvcuda.dll':
            raise ValueError('Only the cached-artifact CUDA driver is allowed')
        result=loader(name,*args,**kwargs)
        if not isinstance(result,NativeLibrary) or result.journal is not journal:
            raise ValueError('The original native API observer must be active before any driver call')
        return result
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(NativeFunction,'__call__',checked))
        if loader is not None:stack.enter_context(patch.object(C,'WinDLL',library))
        yield
        if len(allocation)!=3 or uploads!=2*count or launches!=count:
            raise ValueError('Incomplete observed CUDA sequence')
