"""nvJitLink 12.4 CUBIN-in-memory primitive; caller must provide a bounded Job.

No DLL loading, source compilation, driver calls, retry or cache publication here.
The high-level origin/Job/toolchain admission is deliberately a separate gate.
"""
import ctypes as C
import hashlib
from pathlib import Path
from portable_partition_object import validate_object
from portable_device_linker import validate_cubin

OPTIONS=['-arch=sm_86','-verbose']
INPUT_CUBIN=1
LIMIT=2147483648
TOOL_VERSION='12.4.127'
TOOL_SHA256='2da9da786b85c100ba122f931a49c5c1eda83c32e3fa36814c2ef470e45fa9b1'
ARCHIVE_SHA256='d8f4086215f482263dbfbe47a3580e88acbcdacbb284f8aa0c21a8fe408e671d'


class JitLinkError(RuntimeError):
    def __init__(self,diagnostic):
        self.diagnostic=diagnostic
        super().__init__(diagnostic['failure'])



def validate_library(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Expected a regular pinned JIT linker DLL')
    raw=path.read_bytes()
    if not raw.startswith(b'MZ') or hashlib.sha256(raw).hexdigest()!=TOOL_SHA256:raise ValueError('JIT linker DLL is not the pinned NVIDIA component')
    return dict(version=TOOL_VERSION,sha256=TOOL_SHA256,archive_sha256=ARCHIVE_SHA256,bytes=len(raw))


def symbol(name):return 'nvJitLinkVersion' if name=='Version' else '__nvJitLink'+name+'_12_4'


def bind(lib):
    signatures=dict(Version=[C.POINTER(C.c_uint),C.POINTER(C.c_uint)],
        Create=[C.POINTER(C.c_void_p),C.c_uint32,C.POINTER(C.c_char_p)],Destroy=[C.POINTER(C.c_void_p)],
        AddData=[C.c_void_p,C.c_int,C.c_void_p,C.c_size_t,C.c_char_p],Complete=[C.c_void_p],
        GetLinkedCubinSize=[C.c_void_p,C.POINTER(C.c_size_t)],GetLinkedCubin=[C.c_void_p,C.c_void_p],
        GetErrorLogSize=[C.c_void_p,C.POINTER(C.c_size_t)],GetErrorLog=[C.c_void_p,C.c_void_p],
        GetInfoLogSize=[C.c_void_p,C.POINTER(C.c_size_t)],GetInfoLog=[C.c_void_p,C.c_void_p])
    for name,args in signatures.items():
        function=getattr(lib,symbol(name));function.argtypes=args;function.restype=C.c_int


def link_cubin(lib,raw):
    if not isinstance(raw,bytes):raise ValueError('Immutable object bytes required')
    input_metadata=validate_object(raw);bind(lib);handle=C.c_void_p();artifact=None
    diagnostic=dict(events=[],error_log='',info_log='',log_errors=[],cleanup_error=None,failure=None,
        api_version=None,options=list(OPTIONS),input=input_metadata,artifact=None,
        source_origin_verified=False,containment_verified=False,calculation_verified=False,program_driver_api_calls=0)
    def call(name,*args):
        code=int(getattr(lib,symbol(name))(*args));diagnostic['events'].append(dict(api=symbol(name),return_code=code));return code
    def checked(name,*args):
        code=call(name,*args)
        if code:raise RuntimeError(symbol(name)+' failed: '+str(code))
    logs_collected=False
    def logs():
        nonlocal logs_collected
        if logs_collected:return
        logs_collected=True
        for kind in ('Error','Info'):
            size=C.c_size_t()
            try:
                checked('Get'+kind+'LogSize',handle,C.byref(size))
                if size.value>=LIMIT:raise ValueError('Link log exceeds bounded memory policy')
                if size.value:
                    buffer=C.create_string_buffer(size.value);checked('Get'+kind+'Log',handle,buffer)
                    diagnostic[kind.lower()+'_log']=buffer.raw.rstrip(b'\0').decode('utf-8',errors='replace')
            except (ValueError,RuntimeError) as error:diagnostic['log_errors'].append(str(error))
    try:
        major,minor=C.c_uint(),C.c_uint();checked('Version',C.byref(major),C.byref(minor))
        diagnostic['api_version']=[major.value,minor.value]
        if diagnostic['api_version']!=[12,4]:raise ValueError('Expected nvJitLink12.4 API')
        options=(C.c_char_p*len(OPTIONS))(*(value.encode('ascii') for value in OPTIONS))
        checked('Create',C.byref(handle),len(OPTIONS),options)
        if not handle.value:raise ValueError('Link API returned an empty handle')
        data=C.create_string_buffer(raw);checked('AddData',handle,INPUT_CUBIN,data,len(raw),b'module.relocatable.cubin')
        checked('Complete',handle);logs()
        if diagnostic['log_errors']:raise RuntimeError('Link API log capture failed')
        if diagnostic['error_log']:raise RuntimeError('Link API returned an error log on success')
        size=C.c_size_t();checked('GetLinkedCubinSize',handle,C.byref(size))
        if not 0<size.value<LIMIT:raise ValueError('Invalid linked image size for bounded Job')
        output=C.create_string_buffer(size.value);checked('GetLinkedCubin',handle,output)
        artifact=output.raw;diagnostic['artifact']=validate_cubin(artifact)
    except (ValueError,RuntimeError,OSError) as error:
        diagnostic['failure']=str(error)
        if handle.value:logs()
    finally:
        if handle.value:
            try:
                code=call('Destroy',C.byref(handle))
                if code or handle.value:diagnostic['cleanup_error']='nvJitLinkDestroy did not return success and clear its handle'
            except (ValueError,RuntimeError,OSError) as error:diagnostic['cleanup_error']=str(error)
    if diagnostic['cleanup_error'] and not diagnostic['failure']:diagnostic['failure']=diagnostic['cleanup_error']
    if diagnostic['failure']:raise JitLinkError(diagnostic)
    return artifact,diagnostic
