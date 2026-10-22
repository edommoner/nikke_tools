"""Bounded source-only phase diagnostics preserve source and failure evidence."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_phase_codegen import generate,wrapper,PHASES

CLOSURE={name:'fixed' for name in ('gpu/program_phases.slang','gpu/event_runtime.slang','gpu/world_projectile_resident_entry.slang')}


class PhaseCodegenTests(unittest.TestCase):
    def setup_paths(self,folder):
        root=Path(folder);tool=root/('tool/bin/slangc.exe' if sys.platform=='win32' else 'tool/bin/slangc');tool.parent.mkdir(parents=True);tool.write_bytes(b'fixed compiler')
        return root,root/'out'

    def runner(self,argv,**kwargs):
        self.assertEqual(kwargs,dict(capture_output=True,timeout=60))
        self.assertIn('precise',argv);self.assertEqual(argv[argv.index('-entry')+1],'portablePhase')
        Path(argv[argv.index('-o')+1]).write_bytes(b'void portablePhase() { helper(); }\nvoid helper() {}\n')
        Path(argv[argv.index('-reflection-json')+1]).write_text('{}')
        return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')

    def invoke(self,root,out,**kwargs):
        return generate(root,'gpu/world_entry_reload_resident_entry.slang',out,package_id='fixed-package',source_hashes=kwargs.pop('source_hashes',lambda _:dict(CLOSURE)),compiler_root=root/'tool',runner=kwargs.pop('runner',self.runner),**kwargs)

    def test_phase_wrappers_call_only_the_chosen_shared_body(self):
        for name,body in PHASES.items():
            code=wrapper(ROOT,'gpu/world_entry_reload_resident_entry.slang',name)
            self.assertIn(body,code);self.assertIn('#define portableEvents unusedFullPortableEvents',code)
            for other,other_body in PHASES.items():
                if other!=name:self.assertNotIn(other_body,code)
        with self.assertRaises(ValueError):wrapper(ROOT,'gpu/source.slang','unknown')

    def test_paired_generation_records_all_artifacts_without_support_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            root,out=self.setup_paths(folder);r=self.invoke(root,out)
            self.assertTrue(r['passed']);self.assertEqual(r['slang_codegen_calls'],6)
            self.assertEqual(list(r['phases']),list(PHASES));self.assertFalse(r['calculation_verified']);self.assertFalse(r['executable_battle_verified'])
            self.assertEqual(r['gpu_calls'],dict(build=0,execute=0));self.assertEqual(r['nvrtc_calls'],0)
            for row in r['phases'].values():self.assertEqual(set(row['targets']),{'cuda','metal'})
            original=(out/'report.json').read_bytes()
            with self.assertRaises(FileExistsError):self.invoke(root,out)
            self.assertEqual((out/'report.json').read_bytes(),original)

    def test_source_mutation_stops_before_the_next_phase(self):
        with tempfile.TemporaryDirectory() as folder:
            root,out=self.setup_paths(folder)
            with self.assertRaisesRegex(ValueError,'source changed'):
                self.invoke(root,out,source_hashes=unittest.mock.Mock(side_effect=[dict(CLOSURE),{}]))
            r=json.loads((out/'report.json').read_text());self.assertFalse(r['passed']);self.assertEqual(r['slang_codegen_calls'],2)

    def test_compile_failure_retains_partial_artifact_and_logs(self):
        with tempfile.TemporaryDirectory() as folder:
            root,out=self.setup_paths(folder)
            def fail(argv,**kwargs):
                Path(argv[argv.index('-o')+1]).write_bytes(b'partial source')
                return SimpleNamespace(returncode=7,stdout=b'compiler stdout',stderr=b'compiler stderr')
            with self.assertRaisesRegex(RuntimeError,'generation failed'):self.invoke(root,out,runner=fail)
            self.assertEqual((out/'init.cu').read_bytes(),b'partial source')
            self.assertEqual((out/'init.cuda.stderr.log').read_bytes(),b'compiler stderr')
            r=json.loads((out/'report.json').read_text());self.assertFalse(r['passed']);self.assertEqual(r['slang_codegen_calls'],1)

    def test_timeout_retains_partial_output_and_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            root,out=self.setup_paths(folder)
            def timeout(argv,**kwargs):raise subprocess.TimeoutExpired(argv,60,output=b'partial stdout',stderr=b'partial stderr')
            with self.assertRaises(subprocess.TimeoutExpired):self.invoke(root,out,runner=timeout)
            r=json.loads((out/'report.json').read_text());self.assertEqual(r['slang_codegen_calls'],1)
            self.assertTrue(r['phases']['init']['targets']['cuda']['timed_out'])
            self.assertEqual((out/'init.cuda.stdout.log').read_bytes(),b'partial stdout')

    def test_missing_artifact_or_wrong_source_closure_is_rejected(self):
        for missing in (True,False):
            with self.subTest(missing=missing),tempfile.TemporaryDirectory() as folder:
                root,out=self.setup_paths(folder)
                runner=lambda *a,**kw:SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
                with self.assertRaises(ValueError):self.invoke(root,out,runner=runner,source_hashes=lambda _:dict(CLOSURE) if missing else {})
                self.assertFalse(json.loads((out/'report.json').read_text())['passed'])


if __name__=='__main__':unittest.main()
