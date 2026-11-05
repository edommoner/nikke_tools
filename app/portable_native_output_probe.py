"""Tiny owned-file Win32 write probe for the existing native CPU smoke."""
import ctypes as C
import hashlib,json,sys
from pathlib import Path

MARKER=b'nikke-native-gate-v1'
PROBE_NAME='native-smoke.probe.partial.cubin'


def probe(path,*,dll=None,get_error=None):
    path=Path(path)
    if not path.is_absolute() or path.name!=PROBE_NAME:raise ValueError('Expected the owned absolute native smoke probe path')
    if dll is None:dll=C.WinDLL('kernel32',use_last_error=True)
    get_error=get_error or C.get_last_error
    signatures=dict(CreateFileW=([C.c_wchar_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p],C.c_void_p),
        WriteFile=([C.c_void_p,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32),C.c_void_p],C.c_int),
        FlushFileBuffers=([C.c_void_p],C.c_int),CloseHandle=([C.c_void_p],C.c_int))
    for name,(args,result) in signatures.items():
        function=getattr(dll,name);function.argtypes=args;function.restype=result
    record=dict(protocol='native-file-output-v1',api='CreateFileW',status='failed',created=False,written_bytes=0,
        flushed=False,closed=False,failed_operation=None,winerror=None,close_winerror=None,
        expected_bytes=len(MARKER),expected_sha256=hashlib.sha256(MARKER).hexdigest())
    # GENERIC_WRITE, exclusive sharing, CREATE_NEW, FILE_ATTRIBUTE_NORMAL.
    # Never overwrite an existing file or change an ACL/protection setting.
    handle=dll.CreateFileW(str(path),0x40000000,0,None,1,0x80,None)
    if handle in (None,0,C.c_void_p(-1).value):
        record.update(failed_operation='CreateFileW',winerror=int(get_error()));return record
    record['created']=True
    try:
        written=C.c_uint32();buffer=C.create_string_buffer(MARKER)
        succeeded=dll.WriteFile(handle,buffer,len(MARKER),C.byref(written),None);record['written_bytes']=written.value
        if not succeeded:record.update(failed_operation='WriteFile',winerror=int(get_error()))
        else:
            if written.value!=len(MARKER):record['failed_operation']='short_write'
            elif not dll.FlushFileBuffers(handle):record.update(failed_operation='FlushFileBuffers',winerror=int(get_error()))
            else:record['flushed']=True
    finally:
        record['closed']=bool(dll.CloseHandle(handle))
        if not record['closed']:
            record['close_winerror']=int(get_error())
            if record['failed_operation'] is None:record.update(failed_operation='CloseHandle',winerror=record['close_winerror'])
    if record['failed_operation'] is None:record['status']='verified'
    return record


def validate_probe(record,raw):
    if not isinstance(record,dict) or record.get('protocol')!='native-file-output-v1' or record.get('api')!='CreateFileW' or record.get('status')!='verified':raise ValueError('Native output probe did not verify')
    if any(record.get(field) is not True for field in ('created','flushed','closed')) or record.get('written_bytes')!=len(MARKER) or record.get('expected_bytes')!=len(MARKER) or record.get('expected_sha256')!=hashlib.sha256(MARKER).hexdigest() or any(record.get(field) is not None for field in ('failed_operation','winerror','close_winerror')) or raw!=MARKER:
        raise ValueError('Native output probe receipt/bytes mismatch')
    return True


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('One owned probe path required')
    result=probe(sys.argv[1]);print(json.dumps(result,sort_keys=True));raise SystemExit(0 if result['status']=='verified' else 71)
