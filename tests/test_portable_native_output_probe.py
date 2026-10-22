"""Win32 owned-file probe and exact errors with injected file APIs only."""
import ctypes as C,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import portable_native_output_probe as probe


class Function:
    def __init__(self,fn):self.fn=fn
    def __call__(self,*args):return self.fn(*args)


class Files:
    def __init__(self):
        self.error=0;self.fail=None;self.short=False;self.calls=[];self.handle=None;self.path=None
        for name,fn in [('CreateFileW',self.create),('WriteFile',self.write),('FlushFileBuffers',self.flush),('CloseHandle',self.close)]:setattr(self,name,Function(fn))
    def create(self,path,access,share,security,mode,attributes,template):
        self.calls.append(('create',path,access,share,mode,attributes))
        if self.fail=='CreateFileW':self.error=5;return C.c_void_p(-1).value
        self.path=Path(path)
        try:self.handle=self.path.open('xb')
        except FileExistsError:self.error=80;return C.c_void_p(-1).value
        return 123
    def write(self,handle,data,size,written,overlapped):
        self.calls.append(('write',handle,size));count=size-1 if self.short else size
        if self.fail=='WriteFile':self.error=112;return 0
        self.handle.write(C.string_at(data,count));C.cast(written,C.POINTER(C.c_uint32)).contents.value=count;return 1
    def flush(self,handle):
        self.calls.append(('flush',handle));self.handle.flush()
        if self.fail=='FlushFileBuffers':self.error=5;return 0
        return 1
    def close(self,handle):
        self.calls.append(('close',handle));self.handle.close()
        if self.fail=='CloseHandle':self.error=6;return 0
        return 1


class NativeOutputProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name).resolve()/probe.PROBE_NAME;self.files=Files()
    def run_probe(self):return probe.probe(self.path,dll=self.files,get_error=lambda:self.files.error)
    def test_exclusive_write_flush_close_and_actual_bytes_are_required(self):
        record=self.run_probe();self.assertTrue(probe.validate_probe(record,self.path.read_bytes()))
        self.assertEqual(self.files.calls[0],('create',str(self.path),0x40000000,0,1,0x80))
        self.assertEqual([r[0] for r in self.files.calls],['create','write','flush','close'])
        bad=dict(record,written_bytes=19)
        with self.assertRaisesRegex(ValueError,'mismatch'):probe.validate_probe(bad,self.path.read_bytes())
    def test_create_denied_retains_windows_error_and_never_writes_or_closes_invalid_handle(self):
        self.files.fail='CreateFileW';record=self.run_probe()
        self.assertEqual((record['failed_operation'],record['winerror']),('CreateFileW',5));self.assertFalse(self.path.exists())
        self.assertEqual(len(self.files.calls),1)
        with self.assertRaisesRegex(ValueError,'did not verify'):probe.validate_probe(record,b'')
    def test_existing_probe_is_not_overwritten(self):
        self.path.write_bytes(b'existing');record=self.run_probe()
        self.assertEqual(record['winerror'],80);self.assertEqual(self.path.read_bytes(),b'existing')
    def test_write_flush_and_close_errors_remain_failed_and_owned_handle_is_closed(self):
        for operation,error in [('WriteFile',112),('FlushFileBuffers',5),('CloseHandle',6)]:
            with self.subTest(operation=operation):
                self.files=Files();self.files.fail=operation;self.path.unlink(missing_ok=True);record=self.run_probe()
                self.assertEqual((record['failed_operation'],record['winerror']),(operation,error));self.assertEqual(record['status'],'failed')
                self.assertTrue(self.files.handle.closed);self.assertEqual([r[0] for r in self.files.calls].count('close'),1)
    def test_short_write_and_raw_tampering_are_not_success(self):
        self.files.short=True;record=self.run_probe();self.assertEqual(record['failed_operation'],'short_write')
        self.assertTrue(self.files.handle.closed);self.path.unlink();self.files=Files();record=self.run_probe()
        with self.assertRaisesRegex(ValueError,'mismatch'):probe.validate_probe(record,b'wrong')
    def test_only_the_owned_absolute_filename_is_accepted(self):
        for path in (Path('relative')/probe.PROBE_NAME,self.path.with_name('other.bin')):
            with self.subTest(path=path),self.assertRaises(ValueError):probe.probe(path,dll=self.files,get_error=lambda:0)
        self.assertEqual(self.files.calls,[])


if __name__=='__main__':unittest.main()
