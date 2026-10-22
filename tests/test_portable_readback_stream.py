"""Compare all fields with bounded file reads, including changing/corrupt captures."""
import array,contextlib,hashlib,importlib.util,json,struct,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('stream_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
OW=786432*4

class ReadbackStreamTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.capture=Path(t.name)
        self.names=['reject/first','native/middle','reject/last'];data=struct.pack('<IIII',3,10,11,12)
        digest=lambda value:cli.sha(json.dumps(value,sort_keys=True).encode())
        self.parts=[];rows=[]
        for i,name in enumerate(self.names):
            part=struct.pack('<II',0 if i==1 else 64,i)+bytes(OW-8);self.parts.append(part)
            native={'observed':i} if i==1 else {'status':64}
            rows.append(dict(name=name,input_sha256=cli.sha(data[4+i*4:8+i*4]),output_sha256=cli.sha(part),native_sha256=digest(native)))
        self.raw=self.capture/'readback.bin'
        with self.raw.open('wb') as f:
            for p in self.parts:f.write(p)
        output=hashlib.sha256(b''.join(self.parts)).hexdigest()
        (self.capture/'input.bin').write_bytes(data)
        cli.write(self.capture/'evidence.json',dict(input_sha256=cli.sha(data),output_sha256=output,source_sha256={},gpu_execution_verified=True,backend='metal'))
        for suffix in ('cu','metal'):(self.capture/('generated.'+suffix)).write_bytes(b'generated')
        self.m=dict(purpose='sealed',suite='entry-reload-regression',golden=dict(input_sha256=cli.sha(data),source_sha256={},entries=rows,output_sha256=output,generated_normalized=dict(cuda=cli.sha(b'generated'),metal=cli.sha(b'generated'))))
        self.compare=Mock(side_effect=lambda block,domain:dict(observed=block[1]))
        self.reject=Mock()
        self.adapter=types.SimpleNamespace(suite=types.SimpleNamespace(INPUT=1),prepare=lambda:([(n,[10+i],{} if i==1 else None) for i,n in enumerate(self.names)],data),compare=self.compare,validate_rejection=self.reject,cross=types.SimpleNamespace(digest=digest,normalized=cli.sha))

    def audit(self):return cli.compare_readback(self.m,self.capture,self.adapter)

    @contextlib.contextmanager
    def bounded(self):
        original_read=Path.read_bytes;original_open=Path.open;owner=self;self.read_sizes=[]
        def read_bytes(path):
            if path==owner.raw:raise AssertionError('Whole readback read forbidden')
            return original_read(path)
        @contextlib.contextmanager
        def opened(path,*args,**kwargs):
            with original_open(path,*args,**kwargs) as f:
                if path!=owner.raw:yield f;return
                class Reader:
                    def read(self,size=-1):
                        owner.assertGreaterEqual(size,0);owner.assertLessEqual(size,8*1024*1024);owner.read_sizes.append(size);return f.read(size)
                yield Reader()
        with patch.object(Path,'read_bytes',read_bytes),patch.object(Path,'open',opened):yield

    def test_all_bytes_and_case_comparators_preserved_with_bounded_reads(self):
        with self.bounded():
            result=self.audit();records=cli.file_records(self.capture,['readback.bin']);cli.check_records(self.capture,records)
        self.assertTrue(result['calculation_verified']);self.assertEqual(result['entries'],self.m['golden']['entries'])
        self.assertEqual(result['output_sha256'],self.m['golden']['output_sha256']);self.assertEqual(result['native_oracles'],1)
        self.compare.assert_called_once();self.assertEqual(self.reject.call_count,2)
        self.assertIn(OW,self.read_sizes);self.assertEqual(records[0]['bytes'],3*OW)

    def test_corrupt_or_resized_output_rejected_before_native(self):
        for kind in ('short','extra','same_size_changed'):
            with self.subTest(kind=kind):
                with self.raw.open('wb') as f:
                    for part in self.parts:f.write(part)
                    if kind=='extra':f.write(b'x')
                with self.raw.open('r+b') as f:
                    if kind=='short':f.truncate(3*OW-1)
                    elif kind=='same_size_changed':f.seek(3*OW-1);f.write(b'x')
                with self.assertRaisesRegex(ValueError,'evidence/raw mismatch'):self.audit()
                self.compare.assert_not_called();self.reject.assert_not_called()

    def test_change_between_initial_hash_and_consumed_blocks_is_rejected(self):
        def compare(block,domain):
            with self.raw.open('r+b') as f:f.seek(2*OW+100);f.write(b'x')
            return dict(observed=block[1])
        self.compare.side_effect=compare
        with self.assertRaisesRegex(ValueError,'changed during comparison'):self.audit()

    def test_generator_checks_complete_size_and_digest_after_last_case(self):
        for count,digest in ((2,self.m['golden']['output_sha256']),(3,'0'*64),(4,self.m['golden']['output_sha256'])):
            with self.subTest(count=count,digest=digest),self.assertRaisesRegex(ValueError,'changed during comparison'):
                list(cli.readback_parts(self.raw,count,OW,digest))

if __name__=='__main__':unittest.main()
