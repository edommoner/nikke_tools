"""Both sequence adapters retain all rows; failure never publishes a prefix."""
import hashlib,json,os,struct,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import portable_partitioned_transport as partitioned


def digest(raw):return hashlib.sha256(raw).hexdigest()


class PartitionedTransportTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name).resolve()
        (self.root/'research').mkdir();(self.root/'gpu').mkdir();(self.root/'research/summarize-portable-cross-gpu.py').write_text('import hashlib\ndef normalized(raw):return hashlib.sha256(raw).hexdigest()\n')
        self.source='gpu/probe.slang';(self.root/self.source).write_bytes(b'sealed source')
        self.outputs={k:self.root/('generated.'+k) for k in ('metal','cuda')}
        for k,p in self.outputs.items():p.write_bytes(k.encode())
        self.hashes={self.source:digest(b'sealed source')};self.generated={k:digest(p.read_bytes()) for k,p in self.outputs.items()}
        self.packed=struct.pack('<11I',5,0,10,1,11,0xffffffff,12,3,13,4,14)
        self.expected=b''.join(struct.pack('<III',x,x^0xffffffff,y) for x,y in ((0,10),(1,11),(0xffffffff,12),(3,13),(4,14)))
        self.dest=self.root/'readback.bin';self.seen=[];self.mutate=None;self.bad=None
        self.adapter=SimpleNamespace(ROOT=self.root,READBACK_CHUNK_BYTES=8,
            platform=SimpleNamespace(system=lambda:'Darwin'),validate_composed_stride=Mock(),source_hashes=lambda _:{self.source:digest((self.root/self.source).read_bytes())},
            build=Mock(return_value=(self.outputs,self.hashes)),resident_plan=lambda *a:dict(stride=24),run_metal_command=Mock(side_effect=self.metal),execute_cuda_batches=Mock(side_effect=self.cuda))
        p=patch.dict(os.environ,NIKKE_SLANG_GENERATION_REQUIRED='1',NIKKE_CUDA_CACHE_REQUIRED='1',NIKKE_CUDA_ARTIFACT='cubin');p.start();self.addCleanup(p.stop)

    def sequence(self,batches,paths,backend):
        rows=[]
        for i,(packed,path) in enumerate(zip(batches,paths,strict=True)):
            count,=struct.unpack_from('<I',packed);self.seen.append(count)
            words=struct.unpack('<'+'I'*(len(packed)//4),packed)
            raw=b''.join(struct.pack('<III',x,x^0xffffffff,y) for x,y in zip(words[1::2],words[2::2],strict=True))
            if self.bad=='reordered' and i==1:raw=raw[::-1]
            path.write_bytes(raw)
            transport=dict(cases=count,command_status='completed',input_bytes=len(packed),output_bytes=len(raw),file_readback_chunk_bytes=8)
            if backend=='cuda':transport['readback_stream']=dict(output_bytes=len(raw),output_sha256=digest(raw),chunk_bytes=8,chunks=(len(raw)+7)//8)
            if self.bad=='receipt' and i==1:transport['cases']=True
            rows.append(transport)
        if self.mutate:self.mutate()
        return rows[:-1] if self.bad=='missing' else rows

    def metal(self,argv):
        self.assertIn('--batches',argv);self.assertEqual(argv[-1],'24')
        manifest=json.loads(Path(argv[3]).read_text());batches=[Path(r['input']).read_bytes() for r in manifest]
        rows=self.sequence(batches,[Path(r['output']) for r in manifest],'metal')
        return SimpleNamespace(returncode=1 if self.bad=='process' else 0,stdout=json.dumps(dict(batches=rows,pipeline_instances=1,buffer_allocations=3)),stderr='failed batch' if self.bad=='process' else '')

    def cuda(self,source,entry,batches,sizes,counts,**kwargs):
        self.assertEqual(counts,[2,2,1]);self.assertEqual(sizes,[24,24,12]);self.assertEqual(kwargs['resident'],dict(stride=24))
        return [None]*len(batches),self.sequence(batches,kwargs['output_paths'],'cuda')

    def run_transport(self,backend='metal'):
        return partitioned.execute(self.source,'entry',self.packed,2,3,backend,readback_path=self.dest,
            expected_input_sha256=digest(self.packed),expected_output_sha256=digest(self.expected),expected_source_sha256=self.hashes,
            expected_generated_normalized=self.generated,batch_size=2,adapter=self.adapter)

    def test_both_adapters_keep_all_rows_status_words_tail_and_full_hash(self):
        for name in ('metal','cuda'):
            self.dest=self.root/('readback-'+name);self.seen=[]
            raw,proof=self.run_transport(name)
            self.assertIsNone(raw);self.assertEqual(self.dest.read_bytes(),self.expected);self.assertEqual(self.seen,[2,2,1])
            self.assertEqual(proof['input_sha256'],digest(self.packed));self.assertEqual(proof['output_sha256'],digest(self.expected))
            self.assertEqual(proof['transport']['cases'],5);self.assertEqual(proof['plan']['maximum_output_buffer_bytes'],24)
            self.assertEqual(proof['plan']['maximum_runtime_buffer_bytes'],48);self.assertTrue(proof['gpu_execution_verified']);self.assertFalse(proof['calculation_verified'])
            self.assertEqual([r['first_case'] for r in proof['dispatches']],[0,2,4])
            self.assertFalse(self.dest.with_name(self.dest.name+'.partial').exists())
        self.assertEqual(self.adapter.run_metal_command.call_count,1);self.assertEqual(self.adapter.execute_cuda_batches.call_count,1)
        self.assertEqual(self.adapter.build.call_count,2)

    def test_plan_reframes_only_headers_and_accounts_for_retained_disk_copies(self):
        p=partitioned.plan(self.packed,2,3,2,runtime_stride=24);chunks=partitioned.split(self.packed,p)
        self.assertEqual(struct.pack('<I',5)+b''.join(c[4:] for c in chunks),self.packed)
        self.assertEqual(p['staging_bytes'],2*len(self.expected)+sum(map(len,chunks)))
        for size in (0,True,1.5,65537):
            with self.subTest(size=size),self.assertRaises(ValueError):partitioned.plan(self.packed,2,3,size)
        with self.assertRaises(ValueError):partitioned.plan(self.packed[:-1],2,3,2)
        p['batches'].reverse()
        with self.assertRaises(ValueError):partitioned.split(self.packed,p)

    def test_plan_for_full_106_keeps_every_row_and_reduces_maximum_allocation(self):
        # Dimension scaling is analytical only; avoid constructing 49MB fixture data.
        p=partitioned.plan(struct.pack('<I',106)+b'\0'*(106*4),1,2064786,16,runtime_stride=143048)
        self.assertEqual(p['input_count'],106);self.assertEqual(sum(r['cases'] for r in p['batches']),106)
        self.assertEqual([r['cases'] for r in p['batches']],[16]*6+[10])
        self.assertEqual(p['output_bytes'],875469264);self.assertEqual(p['maximum_output_buffer_bytes'],132146304)
        self.assertEqual(p['maximum_runtime_buffer_bytes'],2288768)

    def test_failed_or_missing_batch_and_bad_metadata_never_publish(self):
        for bad in ('process','missing','receipt','reordered'):
            self.bad=bad;self.dest=self.root/bad
            with self.subTest(bad=bad),self.assertRaises(RuntimeError):self.run_transport()
            self.assertFalse(self.dest.exists());self.assertTrue(self.dest.with_name(self.dest.name+'.batches').exists())

    def test_source_and_generated_changes_after_execution_keep_failed_parts(self):
        for what in ('source','generated'):
            self.dest=self.root/what;p=self.root/self.source if what=='source' else self.outputs['metal'];old=p.read_bytes()
            self.mutate=lambda p=p:p.write_bytes(b'changed')
            with self.subTest(what=what),self.assertRaises(RuntimeError):self.run_transport()
            self.assertFalse(self.dest.exists());self.assertTrue(self.dest.with_name(self.dest.name+'.partial').exists());p.write_bytes(old)

    def test_existing_or_racing_final_is_never_overwritten(self):
        self.dest.write_bytes(b'original')
        with self.assertRaises(FileExistsError):self.run_transport()
        self.adapter.build.assert_not_called();self.assertEqual(self.dest.read_bytes(),b'original')
        self.dest=self.root/'race';self.mutate=lambda:self.dest.write_bytes(b'other result')
        with self.assertRaises(FileExistsError):self.run_transport()
        self.assertEqual(self.dest.read_bytes(),b'other result');self.assertTrue(self.dest.with_name('race.partial').exists())

    def test_input_source_and_cache_policy_fail_before_generation(self):
        old=self.packed;self.packed=old[:-1]
        with self.assertRaises(ValueError):self.run_transport()
        self.packed=old
        for env in (dict(NIKKE_SLANG_GENERATION_REQUIRED='0'),dict(NIKKE_CUDA_CACHE_REQUIRED='0'),dict(NIKKE_CUDA_ARTIFACT='ptx')):
            with self.subTest(env=env),patch.dict(os.environ,env),self.assertRaises(ValueError):self.run_transport('cuda')
        self.adapter.build.assert_not_called();self.assertFalse(self.dest.exists())

    def test_unavailable_disk_stops_before_generation_or_claiming_any_output(self):
        with patch('portable_capture_storage.space_status',return_value=dict(passed=False)),self.assertRaises(RuntimeError):self.run_transport()
        self.adapter.build.assert_not_called();self.assertFalse(self.dest.with_name(self.dest.name+'.batches').exists())

    def test_readbacks_are_joined_in_chunks_without_whole_output_reads(self):
        original=Path.read_bytes
        def bounded(path):
            if path.suffix=='.out' or path.name.endswith('.partial'):raise AssertionError('Whole readback read forbidden')
            return original(path)
        with patch.object(Path,'read_bytes',bounded):self.run_transport()
        self.assertEqual(self.dest.read_bytes(),self.expected)

    def test_modified_input_after_dispatch_cannot_be_promoted_by_matching_output(self):
        self.mutate=lambda:(self.dest.with_name(self.dest.name+'.batches')/'0.in').write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError,'input changed'):self.run_transport()
        self.assertFalse(self.dest.exists())

    def test_diagnostic_cli_preserves_original_functions_and_rejects_cuda_before_preflight(self):
        import ast
        import portable_partitioned_cli as controller
        original='from types import SimpleNamespace\nSUITES={"fixed":42}\ndef native_value(x):\n return x*2\ndef main(argv=None):\n return argv\nif __name__ == "__main__":\n main()\n'
        before=ast.parse(original);after=ast.parse(controller.patched_cli(original))
        f=lambda tree,name:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        self.assertEqual(ast.dump(f(before,'native_value')),ast.dump(f(after,'native_value')))
        renamed=f(after,'_pre_partitioned_main');renamed.name='main';self.assertEqual(ast.dump(f(before,'main')),ast.dump(renamed))
        c=SimpleNamespace(verify_package=Mock())
        with self.assertRaises(ValueError):controller.run(c,self.root/'new','cuda',16,60)
        c.verify_package.assert_not_called()


if __name__=='__main__':unittest.main()
