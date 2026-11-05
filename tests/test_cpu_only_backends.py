"""Removed device backends must fail before building or allocating outputs."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_backend,portable_detail,portable_slang_generation

class CpuOnlyBackends(unittest.TestCase):
    def test_removed_transports_fail_before_input_or_source_access(self):
        for backend in ('metal','cuda','webgpu'):
            with self.subTest(backend=backend),self.assertRaisesRegex(ValueError,'native backend'):
                portable_backend.execute('missing.slang','portableEvents',b'',1,1,backend)
        self.assertFalse(hasattr(portable_backend,'execute_cuda'))
        self.assertFalse(hasattr(portable_backend,'run_metal_command'))

    def test_only_native_and_browser_product_backends_are_registered(self):
        self.assertEqual(portable_detail.BACKENDS,{'native_detail':'native','browser_detail':'browser'})

    def test_generation_rejects_removed_targets_before_compiler_access(self):
        for target in ('cuda','metal','wgsl','webgpu'):
            with self.subTest(target=target),self.assertRaisesRegex(ValueError,'Unsupported generation target'):
                portable_slang_generation.build(Path('/missing'),'missing.slang','portableEvents',target=target)
