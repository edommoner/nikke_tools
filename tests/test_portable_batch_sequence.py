"""Batch boundaries preserve identity, failure status, and ordered wire hashes."""
import array,hashlib,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_runtime as runtime
import portable_backend as backend

class DispatchSequenceTests(unittest.TestCase):
    def setUp(self):
        self.limits=patch.dict(runtime.L,dict(BATCH=2,INPUT_WORDS=2,OUTPUT_WORDS=1));self.limits.start();self.addCleanup(self.limits.stop)
    def programs(self,n):return [(array.array('I',[i,0]),dict(identity=i)) for i in range(n)]
    def replies(self,source,entry,batches,iw,ow,selected):
        result=[]
        for packed in batches:
            count,=struct.unpack_from('<I',packed);self.assertLessEqual(count,2)
            words=struct.unpack('<'+'I'*(len(packed)//4),packed);raw=struct.pack('<'+'I'*count,*words[1::2])
            result.append((raw,dict(transport=dict(cases=count,command_status='completed',gpu_seconds=.1),source_sha256={'source':'fixed'},generated_sha256={'metal':'fixed'},input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),gpu_execution_verified=True,backend=selected)))
        return result
    def test_more_than_original_batch_capacity_keeps_all_input_output_words(self):
        p=self.programs(2050)
        with patch.object(runtime,'execute_batches',side_effect=self.replies) as execute:
            raw,e=runtime.dispatch_programs(p)
        self.assertEqual(struct.unpack('<2050I',raw),tuple(range(2050)))
        self.assertEqual(len(execute.call_args.args[2]),1025)
        logical=struct.pack('<I',2050)+b''.join(x.tobytes() for x,_ in p)
        self.assertEqual(e['input_sha256'],hashlib.sha256(logical).hexdigest());self.assertEqual(e['output_sha256'],hashlib.sha256(raw).hexdigest())
    def test_last_short_batch_and_order_are_preserved(self):
        with patch.object(runtime,'execute_batches',side_effect=self.replies):raw,e=runtime.dispatch_programs(self.programs(5))
        self.assertEqual([x['transport']['cases'] for x in e['dispatches']],[2,2,1]);self.assertEqual(e['transport']['cases'],5)
    def test_single_batch_uses_existing_transport(self):
        with patch.object(runtime,'execute',return_value=('raw','evidence')) as single,patch.object(runtime,'execute_batches') as many:
            self.assertEqual(runtime.dispatch_programs(self.programs(2)),('raw','evidence'));single.assert_called_once();many.assert_not_called()
    def test_failure_after_boundary_returns_all_ordered_statuses(self):
        decode=lambda words,meta:dict(status=words[0],identity=meta['identity'])
        with patch.object(runtime,'execute_batches',side_effect=self.replies),patch.object(runtime,'decode',side_effect=decode):
            with self.assertRaises(runtime.PortableExecutionError) as caught:runtime.run_programs(self.programs(5))
        self.assertEqual(caught.exception.statuses,[0,1,2,3,4]);self.assertEqual([r['identity'] for r in caught.exception.results],list(range(5)))
    def test_missing_dispatch_cannot_return_partial_success(self):
        with patch.object(runtime,'execute_batches',return_value=[]),self.assertRaises(RuntimeError):runtime.dispatch_programs(self.programs(3))
    def test_changed_source_between_dispatches_fails_closed(self):
        def changed(*args):
            out=self.replies(*args);out[1][1]['source_sha256']={'source':'changed'};return out
        with patch.object(runtime,'execute_batches',side_effect=changed),self.assertRaises(RuntimeError):runtime.dispatch_programs(self.programs(3))
    def test_invalid_batch_sizes_or_empty_inputs_never_dispatch(self):
        with patch.object(runtime,'execute') as one,patch.object(runtime,'execute_batches') as many:
            for size in (0,3,True,1.5):
                with self.assertRaises(ValueError):runtime.dispatch_programs(self.programs(3),batch_size=size)
            with self.assertRaises(ValueError):runtime.dispatch_programs([])
            one.assert_not_called();many.assert_not_called()
    def test_transport_rejects_malformed_later_input_before_compilation(self):
        with patch.object(backend,'build') as build:
            for batches in ([],[b''],[struct.pack('<II',1,9),struct.pack('<I',2)]):
                with self.assertRaises(ValueError):backend.execute_batches('source','entry',batches,1,1)
            build.assert_not_called()
if __name__=='__main__':unittest.main()
