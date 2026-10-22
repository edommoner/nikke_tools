"""Reject unsupported generation-cache requests before capture/CPU work/claim."""
import importlib.util,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('generation_request_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class GenerationRequestTests(unittest.TestCase):
    def test_standalone_request_stops_before_capture_or_preflight(self):
        manifest=dict(suite='ordered-history',purpose='development',golden=dict(source_sha256={'gpu/ordered_history_probe.slang':'unused'}))
        with tempfile.TemporaryDirectory() as folder,patch.object(cli,'verify_package',return_value=manifest),patch.object(cli,'cpu_preflight',side_effect=AssertionError('CPU work must not begin')),patch.dict(os.environ,{'NIKKE_SLANG_GENERATION_CACHE':str(Path(folder)/'cache')}):
            capture=Path(folder)/'capture'
            with self.assertRaisesRegex(ValueError,'resident source'):cli.run_capture(capture,'metal',180)
            self.assertFalse(capture.exists())
            self.assertFalse((Path(folder)/'cache').exists())

    def test_no_request_does_not_require_resident_sources(self):
        with patch.dict(os.environ,{},clear=True):cli.validate_generation_request(dict(golden=dict(source_sha256={})))


if __name__=='__main__':unittest.main()
