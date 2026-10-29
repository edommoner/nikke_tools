"""Witness bytes and fresh semantics cannot authenticate an unseen CUDA envelope."""
import copy,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from test_portable_partitioned_cuda_receipt import c
import test_portable_partitioned_native as fixtures
import portable_partitioned_witness as witness
import portable_partitioned_native as native


class WitnessTests(unittest.TestCase):
    def inputs(self):
        raw=(ROOT/'tests/fixtures/resident-current-cuda-v2-summary.json').read_bytes();s=json.loads(raw)
        g=c.load(ROOT/c.SUITES['coordinate-resident-frames']['golden'])
        m=dict(package_id=s['package_id'],golden=g,suite='coordinate-resident-frames')
        wire=dict(input_count=s['input_count'],output_bytes=s['output_bytes'],logical_view_sha256=s['logical_output_sha256'],raw_joined_output_sha256=s['output_sha256'])
        return raw,m,wire

    def test_exact_summary_binds_complete_current_corpus_and_witness_bytes(self):
        raw,m,w=self.inputs();self.assertEqual(witness.bind_summary(c,raw,m,w)['input_count'],106)
        for key,value in [('input_count',105),('output_bytes',1),('logical_view_sha256','0'*64),('raw_joined_output_sha256','0'*64)]:
            bad=copy.deepcopy(w);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):witness.bind_summary(c,raw,m,bad)
        for key,value in [('package_id','other'),('golden',dict(m['golden'],entries=m['golden']['entries'][:-1]))]:
            bad=copy.deepcopy(m);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):witness.bind_summary(c,raw,bad,w)
        with self.assertRaises(ValueError):witness.bind_summary(c,raw+b' ',m,w)

    def test_explicit_saved_file_entry_uses_the_same_native_comparator(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cli,m,calls,adapter,_=fixtures.NativeAuditTests().fixture(root)
            def invoke():
                return native.compare_readback(cli,m,input_path=root/'input.bin',raw_path=root/'readback.bin.partial',
                    layout=cli.load(root/'readback.bin.batches/plan.json'),batch_size=16,
                    generation=cli.load(root/'generation-preflight.json')['generation']['artifacts'],
                    generated_paths={k:root/'research/portable-build'/('entry.'+s) for k,s in (('cuda','cu'),('metal','metal'))},case_indices=[0])
            result=invoke();self.assertTrue(result['comparison_subset_verified']);self.assertFalse(result['calculation_verified'])
            self.assertEqual(calls[0][:2],('native',0))
            adapter.compare=lambda *a:(_ for _ in ()).throw(AssertionError('fresh semantic failure'))
            self.assertFalse(invoke()['comparison_subset_verified'])

    def test_invalid_budget_never_reads_sources_or_creates_an_audit(self):
        for budget,size in ((0,8),(181,8),(True,8),(180,0),(180,17),(180,True)):
            with self.subTest(budget=budget,size=size),self.assertRaisesRegex(ValueError,'Bounded'):
                witness.run(None,None,None,None,None,None,None,None,budget,size)

    def test_source_binding_preserves_all_calculation_bytes_and_current_generation(self):
        import tempfile
        from portable_partitioned_cli import CURRENT
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ('current','executed'):
                p=root/name/'scripts/nikke_gpu.py';p.parent.mkdir(parents=True);p.write_text('def calculate(): return 1\n')
            cli=SimpleNamespace(ROOT=root/'current')
            g=dict(entries=[dict(name='one')],input_sha256='input',output_sha256='output',source_sha256={'gpu':'same'},generated_normalized={'cuda':'same','metal':'same'})
            m=dict(suite='coordinate-resident-frames',golden=g,partitioned_cuda_execution=dict(schema=CURRENT),files=[dict(path='app/engine_worker.py',sha256='pinned')])
            self.assertTrue(witness.bind_sources(cli,m,root/'executed',m,m,m))
            development=copy.deepcopy(m);development['purpose']='development'
            development['golden']={k:v for k,v in g.items() if k in ('entries','input_sha256','source_sha256')}
            self.assertTrue(witness.bind_sources(cli,m,root/'executed',m,development,m))
            development['golden']['output_sha256']='invented'
            with self.assertRaises(ValueError):witness.bind_sources(cli,m,root/'executed',m,development,m)
            for kind in ('native','generation','witness','mode','cli'):
                own=copy.deepcopy(m);gen=copy.deepcopy(m);old=copy.deepcopy(m)
                if kind=='native':own['files'][0]['sha256']='changed'
                elif kind=='generation':gen['golden']['generated_normalized']['cuda']='other'
                elif kind=='witness':old['golden']['entries']=[]
                elif kind=='mode':own['partitioned_cuda_execution']['schema']='legacy'
                else:(cli.ROOT/'scripts/nikke_gpu.py').write_text('def calculate(): return 2\n')
                with self.subTest(kind=kind),self.assertRaises(ValueError):witness.bind_sources(cli,own,root/'executed',m,gen,old)


if __name__=='__main__':unittest.main()
