"""Explicit generation-only development preflight must not become a GPU proof."""
import contextlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('dev_generation_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
import portable_backend,portable_generation_cache,portable_phase_audit

class DevelopmentGenerationTests(unittest.TestCase):
    def test_default_rejects_development_and_flag_rejects_sealed_before_capture(self):
        for purpose,flag in [('development',False),('sealed',True)]:
            with tempfile.TemporaryDirectory() as folder,patch.object(cli,'verify_package',return_value=dict(purpose=purpose)):
                out=Path(folder)/'capture'
                with self.assertRaises(ValueError):cli.generation_capture(out,development=flag)
                self.assertFalse(out.exists())
    def test_development_is_source_anchored_and_never_calculation_certified(self):
        self.run_case(development=True)
    def test_sealed_generation_still_checks_expected_generated_hashes(self):
        self.run_case(development=False,mutate_normalized=True)
    def test_changed_source_is_rejected_even_for_development(self):
        self.run_case(development=True,mutate_source=True)
    def run_case(self,development,mutate_normalized=False,mutate_source=False):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);paths={k:root/(k+'.source') for k in ('cuda','metal')}
            for p in paths.values():p.write_bytes(b'synthetic generation test')
            hashes={'gpu/test.slang':'frozen'}
            manifest=dict(package_id='test',suite='below-def',purpose='development' if development else 'sealed',golden=dict(source_sha256=hashes,generated_normalized={k:'expected' for k in paths}))
            def build(*a,**k):
                with self.assertRaisesRegex(RuntimeError,'forbidden'):portable_backend.execute('must not execute')
                with self.assertRaisesRegex(RuntimeError,'forbidden'):portable_backend.compile_cuda_artifact('must not compile')
                return paths,({'gpu/test.slang':'changed'} if mutate_source else hashes)
            def copy(out,suite):
                for k,suffix in [('cuda','cu'),('metal','metal')]: (out/('generated.'+suffix)).write_bytes(paths[k].read_bytes())
                (out/'generation-cache.json').write_text('{}')
            with patch.object(cli,'verify_package',return_value=manifest),patch.object(cli,'copy_generated',side_effect=copy),patch.object(cli,'collect'),patch.object(cli,'module',return_value=SimpleNamespace(normalized=lambda raw:'changed' if mutate_normalized else 'expected')),patch.object(portable_backend,'build',side_effect=build),patch.object(portable_generation_cache,'audit_receipt',return_value=dict(hit=True,compiler_invocations=0)),patch.object(portable_phase_audit,'observe',return_value=contextlib.nullcontext()):
                out=root/'capture'
                if mutate_source:
                    with self.assertRaisesRegex(ValueError,'immutable package baseline'):cli.generation_capture(out,development=True)
                    self.assertTrue((out/'failure.json').is_file())
                elif mutate_normalized:
                    with self.assertRaisesRegex(ValueError,'sealed baseline'):cli.generation_capture(out)
                    self.assertTrue((out/'failure.json').is_file())
                else:
                    r=cli.generation_capture(out,development=True);self.assertFalse(r['calculation_verified']);self.assertFalse(r['executable_battle_verified']);self.assertFalse(r['sealed_generated_baseline_verified']);self.assertTrue(r['development_only'])
                    self.assertEqual(json.loads((out/'generation.json').read_text())['source_sha256'],hashes)
    def test_cli_dispatch_preserves_explicit_development_flag(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{},clear=False),patch.object(cli,'generation_capture',return_value={'passed':True}) as generated:
            cli.main(['generation','--develop','--out',folder+'/out','--generation-cache',folder+'/cache'])
            generated.assert_called_once_with(Path(folder)/'out',development=True)

if __name__=='__main__':unittest.main()
