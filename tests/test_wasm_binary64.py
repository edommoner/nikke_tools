"""Hardware WASM differential and product routing, with the soft oracle intact."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import portable_wasm as wasm
import portable_slang_generation as generation
from wasm_binary64_diff import build_and_run


class WasmBinary64Test(unittest.TestCase):
    def test_generated_hardware_matches_soft_oracle(self):
        compiler,_=wasm.toolchain(ROOT)
        if not os.access(compiler,os.X_OK) or not os.access(generation.slang_compiler(ROOT),os.X_OK) or not shutil.which('node'):
            self.skipTest('emsdk, Slang and node required')
        with tempfile.TemporaryDirectory(prefix='wasm-binary64-') as scratch:
            build_and_run(ROOT,Path(scratch),20000000)

    def test_product_selects_hardware_and_checks_source_stability(self):
        hashes={'gpu/test.slang':'fixture'}
        with patch.object(generation,'_build_cpp',return_value=({'cpp':Path('hard.cpp')},hashes)) as build, \
             patch.object(generation,'source_hashes',return_value=hashes) as sources, \
             patch.object(wasm,'build_wasm',return_value=('hardware.wasm',{'identity':'new'})) as compile:
            self.assertEqual(wasm.build_product(ROOT,'gpu/test.slang'),('hardware.wasm',{'identity':'new'}))
            build.assert_called_once_with(ROOT,'gpu/test.slang','portableEvents',native_binary64=True)
            compile.assert_called_once_with(ROOT,Path('hard.cpp'))
            sources.return_value={}
            with self.assertRaisesRegex(RuntimeError,'sources changed'):wasm.build_product(ROOT,'gpu/test.slang')
        self.assertNotIn('-DPORTABLE_NATIVE_BINARY64=1',generation.CPP_FLAGS)
        self.assertIn('-ffp-contract=off',wasm.FLAGS)
