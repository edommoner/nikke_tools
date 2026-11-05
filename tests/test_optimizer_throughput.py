"""Generated-byte cache and bounded source-group scheduling."""
import concurrent.futures,hashlib,json,os,subprocess,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_slang_generation as generation
import portable_detail as detail
from portable_throughput import split_threads
from portable_native import HOST_THREADS
ROOT=Path(__file__).resolve().parents[1]

class CppCache(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        (self.root/'entry.slang').write_text('#include "dep.slang"\n');(self.root/'dep.slang').write_text('// dependency')
        self.compiler=self.root/'slangc';self.compiler.write_bytes(b'compiler')
        self.calls=0
    def run_compiler(self,cmd,**kw):
        self.calls+=1
        return subprocess.CompletedProcess(cmd,0,b'// generated cpp',b'')
    def build(self,entry='main'):
        return generation._build_cpp(self.root,'entry.slang',entry)
    def harness(self):
        from contextlib import ExitStack
        stack=ExitStack();stack.enter_context(patch.object(generation,'slang_compiler',return_value=self.compiler))
        stack.enter_context(patch.object(generation.subprocess,'check_output',return_value=b'v1'))
        stack.enter_context(patch.object(generation.subprocess,'run',side_effect=self.run_compiler));return stack
    def test_hit_corruption_and_missing_receipt(self):
        with self.harness():
            a,h=self.build();self.build();self.assertEqual(self.calls,1)
            a['cpp'].write_bytes(b'corrupt');self.build();self.assertEqual(self.calls,2)
            (a['cpp'].parent/'build.json').write_text('{}');self.build();self.assertEqual(self.calls,3)
            (a['cpp'].parent/'build.json').write_text('bad json');self.build();self.assertEqual(self.calls,4)
            self.assertEqual(a['cpp'].read_bytes(),b'// generated cpp')
    def test_all_identity_axes(self):
        with self.harness():
            paths=[self.build()[0]['cpp']]
            for mutate in [lambda:(self.root/'dep.slang').write_text('// changed dependency'),lambda:self.compiler.write_bytes(b'compiler2')]:
                mutate();paths.append(self.build()[0]['cpp'])
            with patch.object(generation.subprocess,'check_output',return_value=b'v2'):paths.append(self.build()[0]['cpp'])
            paths.append(self.build('other')[0]['cpp'])
            with patch.object(generation,'CPP_FLAGS',(*generation.CPP_FLAGS,'-g0')):paths.append(self.build()[0]['cpp'])
            self.assertEqual(len(set(paths)),6)
    def test_top_source_change_and_compile_failure_do_not_publish(self):
        with self.harness():
            first=self.build()[0]['cpp']
            (self.root/'entry.slang').write_text('// new top source')
            second=self.build()[0]['cpp'];self.assertNotEqual(first,second)
            with patch.object(generation.subprocess,'run',return_value=subprocess.CompletedProcess([],1,b'',b'compiler failed')):
                with self.assertRaisesRegex(RuntimeError,'compiler failed'):self.build('failure')
            self.assertEqual(len(list((self.root/'research/portable-build/cpp').glob('*/build.json'))),2)

    def test_hit_still_rechecks_source_and_generated_guard(self):
        with self.harness():
            self.build()
            hashes=generation.source_hashes(self.root,'entry.slang')
            with patch.object(generation,'source_hashes',side_effect=[hashes,{'x':'b'}]),self.assertRaisesRegex(RuntimeError,'sources changed'):self.build()
            self.assertEqual(self.calls,1)  # The mutation was detected on a cache hit.
            with patch.object(generation,'validate_counter_snapshots',side_effect=ValueError('guard')),self.assertRaisesRegex(ValueError,'guard'):self.build()
    def test_concurrent_identical_publish_generates_once(self):
        with self.harness(),concurrent.futures.ThreadPoolExecutor(4) as pool:
            rows=list(pool.map(lambda _:self.build(),range(4)))
        self.assertEqual(self.calls,1);self.assertEqual(len({str(r[0]['cpp']) for r in rows}),1)

class GroupScheduling(unittest.TestCase):
    def test_split_bounded_proportional_and_small_machines(self):
        for cpus in range(1,33):
            for n in range(1,9):
                budgets=split_threads(list(range(1,n+1)),cpus)
                self.assertTrue(all(b>=1 for b in budgets))
                if n<=cpus:self.assertEqual(sum(budgets),cpus)
                else:self.assertEqual(budgets,[1]*n)
        self.assertEqual(split_threads([24,8],8),[6,2]);self.assertEqual(split_threads([],8),[])
    def test_native_groups_overlap_keep_order_and_contain_failure(self):
        barrier=threading.Barrier(2);seen=[]
        def evaluation(body,**kw):
            plan=dict(source=str(body['group']),input_words=1,output_words=1,backend='native',policy={},explicit_image=False,folder=Path('/tmp')/str(body['id']))
            outcome=yield plan
            return dict(id=body['id'],outcome=outcome)
        def execute(plans):
            seen.append((len(plans),HOST_THREADS.get()));barrier.wait(timeout=5)
            if plans[0]['source']=='1':raise RuntimeError('group failure')
            return ['ok']*len(plans)
        bodies=[dict(id=i,group=i%2) for i in range(6)]
        with patch.object(detail,'_evaluation',side_effect=evaluation),patch.object(detail,'_execute_prepared',side_effect=execute),patch.object(os,'cpu_count',return_value=6):
            rows=detail.evaluate_many(bodies,verification='deferred')
        self.assertEqual(sorted(seen),[(3,3),(3,3)])
        for i,row in enumerate(rows):
            if i%2:self.assertEqual(row,dict(error='group failure'))
            else:self.assertEqual(row['result'],dict(id=i,outcome='ok'))
        self.assertIsNone(HOST_THREADS.get())

    def test_optimize_groups_each_receive_full_bounded_host_budget(self):
        seen=[]
        def evaluation(body,**kw):
            outcome=yield dict(source=str(body['group']),input_words=1,output_words=1,backend='native',policy={},explicit_image=False,folder=Path('/tmp')/str(body['id']))
            return dict(id=body['id'])
        def execute(plans):
            seen.append((len(plans),HOST_THREADS.get()));return ['ok']*len(plans)
        token=HOST_THREADS.set(6)
        try:
            with patch.object(detail,'_evaluation',side_effect=evaluation),patch.object(detail,'_execute_prepared',side_effect=execute):
                rows=detail.evaluate_many([dict(id=i,group=i%2,compute_backend='native_detail') for i in range(16)],verification='deferred')
            self.assertEqual(sorted(seen),[(8,6),(8,6)]);self.assertEqual([r['result']['id'] for r in rows],list(range(16)))
            self.assertEqual(HOST_THREADS.get(),6)
        finally:HOST_THREADS.reset(token)


class ServiceBudget(unittest.TestCase):
    def test_budget_validation_and_context_reset(self):
        import io
        import portable_detail_service as service
        request=dict(action='evaluate_portable_detail_batch',evaluations=[dict(compute_backend='native_detail')],host_threads=1)
        def evaluate(*args,**kw):
            self.assertEqual(HOST_THREADS.get(),1);return []
        with patch.object(sys,'stdin',io.StringIO(json.dumps(request))),patch.object(sys,'stdout',io.StringIO()),patch.object(service,'evaluate_many',side_effect=evaluate):
            service.main()
        self.assertIsNone(HOST_THREADS.get())
        for budget in (0,True,(os.cpu_count() or 1)+1):
            request['host_threads']=budget
            with patch.object(sys,'stdin',io.StringIO(json.dumps(request))),patch.object(sys,'stdout',io.StringIO()),patch.object(service,'evaluate_many') as evaluate,self.assertRaises(SystemExit):
                service.main()
            evaluate.assert_not_called()
