"""CUDA driver events measure kernel execution without changing its program."""
import ctypes as C

class KernelTimer:
    def __init__(self,device):
        self.device=device;self.events=[]
        signatures={'cuEventCreate':[C.POINTER(C.c_void_p),C.c_uint],
            'cuEventRecord':[C.c_void_p,C.c_void_p],'cuEventSynchronize':[C.c_void_p],
            'cuEventElapsedTime':[C.POINTER(C.c_float),C.c_void_p,C.c_void_p],
            'cuEventDestroy_v2':[C.c_void_p]}
        for name,args in signatures.items():
            fn=getattr(device.lib,name);fn.argtypes=args;fn.restype=C.c_int
    def __enter__(self):
        try:
            for _ in range(2):
                event=C.c_void_p();self.device.call('cuEventCreate',C.byref(event),0);self.events.append(event)
            return self
        except BaseException:
            self.__exit__(None,None,None);raise
    def start(self):self.device.call('cuEventRecord',self.events[0],None)
    def stop(self):self.device.call('cuEventRecord',self.events[1],None)
    def elapsed(self):
        self.device.call('cuEventSynchronize',self.events[1]);ms=C.c_float()
        self.device.call('cuEventElapsedTime',C.byref(ms),*self.events);return float(ms.value)
    def __exit__(self,*exc):
        # A failed context may reject cleanup; keep the original kernel error.
        for event in self.events:self.device.lib.cuEventDestroy_v2(event)
        self.events=[]
