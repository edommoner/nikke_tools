"""Optional NVIDIA CUDA selection. Stdlib only; combat remains in the pinned engine."""
from __future__ import annotations
import array,ctypes as C,heapq,os,time
from pathlib import Path

class Cuda:
    def __init__(self):
        self.ctx=C.c_void_p();self.module=C.c_void_p();self.buffers=[]
        self.lib=C.WinDLL('nvcuda.dll') if os.name=='nt' else C.CDLL('libcuda.so.1')
        signatures={'cuInit':[C.c_uint],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],
          'cuDeviceGetName':[C.c_char_p,C.c_int,C.c_int],
          'cuDeviceGetAttribute':[C.POINTER(C.c_int),C.c_int,C.c_int],
          'cuCtxCreate_v2':[C.POINTER(C.c_void_p),C.c_uint,C.c_int],
          'cuCtxDestroy_v2':[C.c_void_p],'cuModuleLoadData':[C.POINTER(C.c_void_p),C.c_void_p],
          'cuModuleGetFunction':[C.POINTER(C.c_void_p),C.c_void_p,C.c_char_p],
          'cuMemAlloc_v2':[C.POINTER(C.c_uint64),C.c_size_t],'cuMemFree_v2':[C.c_uint64],
          'cuMemcpyHtoD_v2':[C.c_uint64,C.c_void_p,C.c_size_t],
          'cuMemcpyDtoH_v2':[C.c_void_p,C.c_uint64,C.c_size_t],
          'cuLaunchKernel':[C.c_void_p,*([C.c_uint]*7),C.c_void_p,C.POINTER(C.c_void_p),C.c_void_p],
          'cuCtxSynchronize':[]}
        for name,args in signatures.items():
            fn=getattr(self.lib,name);fn.argtypes=args;fn.restype=C.c_int
        self.call('cuInit',0);device=C.c_int();self.call('cuDeviceGet',C.byref(device),0)
        name=C.create_string_buffer(256);self.call('cuDeviceGetName',name,256,device)
        self.name=name.value.decode('utf-8','replace')
        major=C.c_int();minor=C.c_int();self.call('cuDeviceGetAttribute',C.byref(major),75,device);self.call('cuDeviceGetAttribute',C.byref(minor),76,device)
        self.compute_capability=(major.value,minor.value)
        try:
            self.call('cuCtxCreate_v2',C.byref(self.ctx),0,device)
            ptx=(Path(__file__).parent/'disjoint.ptx').read_bytes()+b'\0'
            self.call('cuModuleLoadData',C.byref(self.module),C.cast(C.c_char_p(ptx),C.c_void_p))
            self.function=C.c_void_p();self.call('cuModuleGetFunction',C.byref(self.function),self.module,b'expand')
            self.sort_function=C.c_void_p();self.call('cuModuleGetFunction',C.byref(self.sort_function),self.module,b'sort_step')
        except Exception:
            self.close();raise
    def call(self,name,*args):
        code=getattr(self.lib,name)(*args)
        if code:raise RuntimeError(f'CUDA {name}: error {code}')
    def upload(self,data):
        raw=data.tobytes();ptr=C.c_uint64();self.call('cuMemAlloc_v2',C.byref(ptr),max(len(raw),8));self.buffers.append(ptr)
        if raw:self.call('cuMemcpyHtoD_v2',ptr,C.cast(C.c_char_p(raw),C.c_void_p),len(raw))
        return ptr
    def expand(self,states,masks,scores,top=None):
        nc=len(masks);size=len(states)*nc
        inputs=[array.array('I',[v for state in states for v in state[0]]),array.array('I',[state[3] for state in states]),
          array.array('Q',[state[1] for state in states]),array.array('I',[v for mask in masks for v in mask]),array.array('Q',scores)]
        try:
            ptrs=[self.upload(v) for v in inputs]
            padded=1<<(size-1).bit_length() if top else size
            output=array.array('Q',[0])*padded;ptrs.append(self.upload(output))
            args=[*ptrs,C.c_uint(nc),C.c_uint(size)]
            params=(C.c_void_p*len(args))(*(C.cast(C.byref(a),C.c_void_p) for a in args))
            self.call('cuLaunchKernel',self.function,(size+255)//256,1,1,256,1,1,0,None,params,None)
            if top:
                indices=array.array('I',range(padded));index_ptr=self.upload(indices)
                stage=2
                while stage<=padded:
                    stride=stage//2
                    while stride:
                        sort_args=[ptrs[-1],index_ptr,C.c_uint(padded),C.c_uint(stride),C.c_uint(stage)]
                        sort_params=(C.c_void_p*len(sort_args))(*(C.cast(C.byref(a),C.c_void_p) for a in sort_args))
                        self.call('cuLaunchKernel',self.sort_function,(padded+255)//256,1,1,256,1,1,0,None,sort_params,None)
                        stride//=2
                    stage*=2
                length=min(top,size)
                target=(C.c_char*(length*8)).from_buffer(output)
                self.call('cuMemcpyDtoH_v2',C.cast(target,C.c_void_p),ptrs[-1],length*8)
                index_target=(C.c_char*(length*4)).from_buffer(indices)
                self.call('cuMemcpyDtoH_v2',C.cast(index_target,C.c_void_p),index_ptr,length*4)
                return [(int(indices[i]),int(output[i])) for i in range(length) if output[i]]
            self.call('cuCtxSynchronize')
            target=(C.c_char*(size*8)).from_buffer(output)
            self.call('cuMemcpyDtoH_v2',C.cast(target,C.c_void_p),ptrs[-1],size*8)
            return output
        finally:
            for ptr in self.buffers:self.call('cuMemFree_v2',ptr)
            self.buffers=[]
    def close(self):
        if self.ctx.value:self.call('cuCtxDestroy_v2',self.ctx);self.ctx=C.c_void_p()


def cpu_expand(states,masks,scores):
    return [total+scores[i]+1 if (last==0xffffffff or i>last) and not any(a&b for a,b in zip(used,mask)) else 0
            for used,total,_,last in states for i,mask in enumerate(masks)]


def select_teams(body,device=None):
    started=time.perf_counter();backend=body.get('backend','cpu');width=body.get('width',256);count=body.get('teamCount',5)
    if backend not in ('cpu','cuda'):raise ValueError('Unknown selection backend')
    if not isinstance(width,int) or not 1<=width<=4096 or count not in (1,5):raise ValueError('Invalid selection bounds')
    candidates=body['candidates']
    if not isinstance(candidates,list) or len(candidates)>160:raise ValueError('At most 160 candidates')
    names=sorted({n for c in candidates for n in c['squad']})
    if len(names)>256:raise ValueError('At most 256 distinct characters')
    ids={name:i for i,name in enumerate(names)};masks=[];scores=[]
    for candidate in candidates:
        squad,score=candidate['squad'],candidate['damage']
        if len(squad)!=5 or len(set(squad))!=5 or not isinstance(score,int) or not 0<=score<=2**53//5:raise ValueError('Invalid candidate')
        mask=[0]*8
        for name in squad:mask[ids[name]//32]|=1<<(ids[name]%32)
        masks.append(mask);scores.append(score)
    owned_device=device is None;gpu_ms=0;expanded=0
    try:
        if backend=='cuda' and device is None:device=Cuda()
        states=[([0]*8,0,[],0xffffffff)]
        for _ in range(count):
            if not candidates or not states:states=[];break
            mark=time.perf_counter()
            if device:
                selected=device.expand(states,masks,scores,top=width)
            else:
                values=cpu_expand(states,masks,scores)
                selected=[(i,int(values[i])) for i in heapq.nlargest(width,(i for i,v in enumerate(values) if v),key=lambda i:(values[i],-i))]
            gpu_ms+=(time.perf_counter()-mark)*1000;expanded+=len(states)*len(candidates)
            next_states=[]
            for index,value in selected:
                parent,choice=divmod(index,len(candidates));old=states[parent]
                next_states.append(([a|b for a,b in zip(old[0],masks[choice])],value-1,old[2]+[choice],choice))
            states=next_states
        recommendation=None
        if states:
            best=states[0];recommendation={'damage':best[1],'teams':[candidates[i] for i in best[2]]}
        return {'recommendation':recommendation,'backend':backend,'device':device.name if device else 'CPU',
          'expanded':expanded,'expansion_ms':round(gpu_ms,3),'elapsed_ms':round((time.perf_counter()-started)*1000,3),'width':width}
    finally:
        if device and owned_device:device.close()


def probe():
    device=None
    try:
        device=Cuda()
        got=list(device.expand([([0]*8,0,[],0xffffffff)],[[1]+[0]*7],[123]))
        if got!=[124]:raise RuntimeError('GPU self-check mismatch')
        return {'available':True,'device':device.name,'backend':'cuda','verified':True}
    except (OSError,RuntimeError,AttributeError) as exc:return {'available':False,'reason':str(exc),'backend':'cpu'}
    finally:
        if device:device.close()
