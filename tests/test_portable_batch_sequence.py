"""Native batches preserve complete ordered words, hashes and execution identity."""
import array,hashlib,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_runtime as runtime

class DispatchSequenceTests(unittest.TestCase):
    def setUp(self):
        limit=patch.dict(runtime.L,dict(BATCH=2,INPUT_WORDS=2,OUTPUT_WORDS=1));limit.start();self.addCleanup(limit.stop)
    def programs(self,n):return [(array.array('I',[i,0]),dict(identity=i)) for i in range(n)]
    def reply(self,source,entry,packed,iw,ow,selected):
        count,=struct.unpack_from('<I',packed);self.assertLessEqual(count,2)
        words=struct.unpack('<'+'I'*(len(packed)//4),packed);raw=struct.pack('<'+'I'*count,*words[1::2])
        return raw,dict(transport=dict(cases=count,command_status='completed',host_seconds=.1),source_sha256={'source':'fixed'},generated_sha256={'cpp':'fixed'},input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),native_execution_verified=True,gpu_execution_verified=False,backend=selected)
    def test_large_sequence_preserves_all_words_and_logical_hashes(self):
        programs=self.programs(2050)
        with patch.object(runtime,'execute',side_effect=self.reply) as execute:raw,e=runtime.dispatch_programs(programs)
        self.assertEqual(struct.unpack('<2050I',raw),tuple(range(2050)));self.assertEqual(execute.call_count,1025)
        logical=struct.pack('<I',2050)+b''.join(words.tobytes() for words,_ in programs)
        self.assertEqual(e['input_sha256'],hashlib.sha256(logical).hexdigest());self.assertEqual(e['output_sha256'],hashlib.sha256(raw).hexdigest())
    def test_last_short_batch_and_native_time_are_aggregated(self):
        with patch.object(runtime,'execute',side_effect=self.reply):raw,e=runtime.dispatch_programs(self.programs(5))
        self.assertEqual([d['transport']['cases'] for d in e['dispatches']],[2,2,1]);self.assertEqual(e['transport']['cases'],5)
        self.assertAlmostEqual(e['transport']['host_seconds'],.3);self.assertEqual(e['transport']['host_processes'],3)
    def test_single_batch_uses_one_transport(self):
        with patch.object(runtime,'execute',return_value=('raw','evidence')) as execute:self.assertEqual(runtime.dispatch_programs(self.programs(2)),('raw','evidence'));execute.assert_called_once()
    def test_failures_preserve_every_ordered_status(self):
        with patch.object(runtime,'execute',side_effect=self.reply),patch.object(runtime,'decode',side_effect=lambda words,meta:dict(status=words[0],identity=meta['identity'])):
            with self.assertRaises(runtime.PortableExecutionError) as caught:runtime.run_programs(self.programs(5))
        self.assertEqual(caught.exception.statuses,[0,1,2,3,4]);self.assertEqual([r['identity'] for r in caught.exception.results],list(range(5)))
    def test_missing_or_changed_dispatch_fails_closed(self):
        for fault in ('missing','source','native'):
            calls=[]
            def reply(*args):
                calls.append(1);raw,e=self.reply(*args)
                if len(calls)==2:
                    if fault=='missing':raw=b''
                    if fault=='source':e['source_sha256']={'source':'changed'}
                    if fault=='native':e['native_execution_verified']=False
                return raw,e
            with self.subTest(fault=fault),patch.object(runtime,'execute',side_effect=reply),self.assertRaises(RuntimeError):runtime.dispatch_programs(self.programs(3))
    def test_invalid_sizes_and_empty_input_never_execute(self):
        with patch.object(runtime,'execute') as execute:
            for size in (0,3,True,1.5):
                with self.assertRaises(ValueError):runtime.dispatch_programs(self.programs(3),batch_size=size)
            with self.assertRaises(ValueError):runtime.dispatch_programs([])
            execute.assert_not_called()
