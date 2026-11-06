"""Fast deterministic subset; acceptance-sized runs use native_binary64_diff.py."""
import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from native_binary64_diff import build_and_run


class NativeBinary64Test(unittest.TestCase):
    def test_generated_hardware_matches_soft_oracle(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='binary64-test-') as scratch:
            build_and_run(root, Path(scratch), 10000)


class NativeBinary64RoutingTest(unittest.TestCase):
    def test_define_is_native_only_and_in_generation_identity(self):
        import json
        import subprocess
        from unittest.mock import patch
        import portable_slang_generation as generation
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'entry.slang').write_text('// fixture')
            compiler=root/'slangc';compiler.write_text('fixture')
            calls=[]
            def compile_cpp(cmd, **kwargs):
                calls.append(cmd)
                return subprocess.CompletedProcess(cmd,0,b'// generated',b'')
            with patch.object(generation,'slang_compiler',return_value=compiler),patch.object(generation,'cpp_compiler_identity',return_value={'fixture':True}),patch.object(generation.subprocess,'run',side_effect=compile_cpp):
                default,_=generation.build(root,'entry.slang','main',target='cpp')
                native,_=generation._build_cpp(root,'entry.slang','main',native_binary64=True)
                generation._build_cpp(root,'entry.slang','main',native_binary64=True)
            self.assertEqual(len(calls),2)
            self.assertNotEqual(default['cpp'],native['cpp'])
            self.assertNotIn('-DPORTABLE_NATIVE_BINARY64=1',calls[0])
            self.assertIn('-DPORTABLE_NATIVE_BINARY64=1',calls[1])
            self.assertIn('-DPORTABLE_NATIVE_BINARY64=1',json.loads((native['cpp'].parent/'build.json').read_text())['flags'])
