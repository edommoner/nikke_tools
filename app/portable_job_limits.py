"""Shared Windows x64 Job extended-limit ABI and read-only inspection."""
import ctypes as C


class BasicLimitInformation(C.Structure):
    _fields_=[('process_time',C.c_int64),('job_time',C.c_int64),('flags',C.c_uint32),
              ('min_ws',C.c_size_t),('max_ws',C.c_size_t),('active_limit',C.c_uint32),
              ('affinity',C.c_size_t),('priority',C.c_uint32),('scheduling',C.c_uint32)]


class IOInformation(C.Structure):
    _fields_=[(name,C.c_uint64) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]


class ExtendedLimitInformation(C.Structure):
    _fields_=[('basic',BasicLimitInformation),('io',IOInformation),('process_mem',C.c_size_t),
              ('job_mem',C.c_size_t),('peak_process',C.c_size_t),('peak_job',C.c_size_t)]


def read_job_limits(dll,handle,info_type=ExtendedLimitInformation):
    if C.sizeof(C.c_void_p)!=8:raise RuntimeError('Validation requires Windows x64 Job ABI')
    dll.QueryInformationJobObject.argtypes=[C.c_void_p,C.c_int,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32)]
    dll.QueryInformationJobObject.restype=C.c_int
    limits=info_type();returned=C.c_uint32()
    if not dll.QueryInformationJobObject(handle,9,C.byref(limits),C.sizeof(limits),C.byref(returned)):
        raise C.WinError(C.get_last_error())
    if returned.value!=C.sizeof(limits):raise RuntimeError('Incomplete Windows Job extended-limit response')
    return dict(job_peak_memory_bytes=int(limits.peak_job),job_memory_limit_bytes=int(limits.job_mem) if limits.basic.flags&0x200 else None)
