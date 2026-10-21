"""Native revival prerequisites; GPU and portable admission remain forbidden."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend,portable_runtime,portable_reference,detail_gpu
from portable_revive_cases import fixtures
from world_revive_native import observe
from world_projectile_native import observe as unobserved
from portable_revive_contracts import verify
s=importlib.util.spec_from_file_location('revive_reference_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class RevivalReferenceTests(unittest.TestCase):
    def test_literal_construction_and_all_native_contracts_without_packing_or_gpu(self):
        from calculator import timeline
        def forbidden(*a,**kw):raise AssertionError('Native/GPU work forbidden in literal construction')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_runtime,'compile_program',forbidden),patch.object(portable_backend,'execute',forbidden):cases=fixtures()
        self.assertEqual(len(cases),26);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for c in cases:
                with self.subTest(c['name']):
                    native,_=observe(c);self.assertTrue(verify(c,native)['verified'])
        self.assertEqual(cases,before)

    def test_observer_preserves_entire_existing_native_result_and_trace(self):
        for c in fixtures():
            plain,trace=unobserved(c);recorded,recorded_trace=observe(c)
            events=recorded.pop('revival_events')
            self.assertEqual(bool(events),c['name']!='revive-alive-noop')
            self.assertEqual(recorded,plain);self.assertEqual(recorded_trace,trace)

    def test_false_contract_retains_failure_and_cannot_replace_it(self):
        modules=dict(zip(portable_reference.REFERENCES['revive'],[
            SimpleNamespace(fixtures=lambda:[dict(name='bad')]),
            SimpleNamespace(observe=lambda c:({},[])),
            SimpleNamespace(verify=lambda c,n:dict(verified=False))]))
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'proof.json'
            with patch.object(portable_reference,'source_identity',return_value={}),patch.object(portable_reference.importlib,'import_module',side_effect=modules.__getitem__):
                with self.assertRaisesRegex(ValueError,'not verified'):
                    portable_reference.run_reference('revive',out,write=cli.write,forbid_gpu=cli.forbid_gpu)
                original=out.read_bytes();r=json.loads(original)
                self.assertFalse(r['passed']);self.assertFalse(r['gpu_supported']);self.assertFalse(r['calculation_verified'])
                self.assertEqual(r['current_case'],'bad');self.assertEqual(r['gpu_calls'],dict(build=0,execute=0))
                with self.assertRaises(FileExistsError):portable_reference.run_reference('revive',out,write=cli.write,forbid_gpu=cli.forbid_gpu)
                self.assertEqual(out.read_bytes(),original)

    def test_guarded_gpu_or_packing_attempt_cannot_pass_native_stage(self):
        for attempt in (lambda:portable_backend.execute('x',b''),lambda:portable_runtime.execute('x',b''),lambda:portable_runtime.compile_program([],[],[],[]),lambda:detail_gpu.compile_effects([],[])):
            def factory():attempt();return []
            modules=dict(zip(portable_reference.REFERENCES['revive'],[SimpleNamespace(fixtures=factory),SimpleNamespace(),SimpleNamespace()]))
            with tempfile.TemporaryDirectory() as folder,patch.object(portable_reference,'source_identity',return_value={}),patch.object(portable_reference.importlib,'import_module',side_effect=modules.__getitem__):
                out=Path(folder)/'blocked.json'
                with self.assertRaisesRegex(RuntimeError,'forbidden'):
                    portable_reference.run_reference('revive',out,write=cli.write,forbid_gpu=cli.forbid_gpu)
                self.assertFalse(json.loads(out.read_text())['cpu_reference_verified'])

    def test_source_or_literal_mutation_cannot_be_promoted_to_verified(self):
        for mutate_source in (True,False):
            def observe(c):
                if not mutate_source:c['changed']=True
                return {},[]
            modules=dict(zip(portable_reference.REFERENCES['revive'],[
                SimpleNamespace(fixtures=lambda:[dict(name='mutated')]),SimpleNamespace(observe=observe),
                SimpleNamespace(verify=lambda c,n:dict(verified=True))]))
            sources=[{'source':'before'},{'source':'after'}] if mutate_source else [{},{}]
            with tempfile.TemporaryDirectory() as folder,patch.object(portable_reference,'source_identity',side_effect=sources),patch.object(portable_reference.importlib,'import_module',side_effect=modules.__getitem__):
                out=Path(folder)/'mutation.json'
                with self.assertRaisesRegex(ValueError,'changed'):
                    portable_reference.run_reference('revive',out,write=cli.write,forbid_gpu=cli.forbid_gpu)
                report=json.loads(out.read_text());self.assertFalse(report['passed'])
                self.assertEqual(report['cases'][0]['input_sha256'],portable_reference.digest(dict(name='mutated')))

if __name__=='__main__':unittest.main()
