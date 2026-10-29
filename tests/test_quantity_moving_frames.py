"""Same complete moving battle and existing generic Frame storage tests."""
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('quantity_moving_frame_contract',ROOT/'tests/test_moving_frames.py')
shared=importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)

class SharedFrameStorageTests(shared.SharedFrameStorageTests):
    pass

class QuantityMovingFramesTests(unittest.TestCase):
    def test_current_seal_keeps_all_inputs_outputs_native_and_only_reviewed_shader_delta(self):
        import json,hashlib
        import nikke_gpu
        from portable_backend import source_hashes
        old=json.loads((ROOT/nikke_gpu.SUITES['moving-frames']['golden']).read_text())
        raw=(ROOT/nikke_gpu.SUITES['moving-visited']['golden']).read_bytes();new=json.loads(raw)
        for key in ('input_sha256','output_sha256','entries'):self.assertEqual(new[key],old[key])
        self.assertEqual(new['source_sha256'],source_hashes(nikke_gpu.SUITES['moving-visited']['source']))
        before=old['source_sha256'];after=new['source_sha256']
        self.assertEqual(set(after)-set(before),{'gpu/quantity_visited.slang'})
        self.assertEqual({name for name in before if before[name]!=after.get(name)},{'gpu/quantity_runtime.slang'})
        cert=json.loads((ROOT/'research/portable-compiler-full--moving-visited-source-certificate.json').read_text())
        self.assertEqual(cert['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(cert['source_sha256'],after)
        self.assertEqual(cert['generated_normalized'],new['generated_normalized'])
        self.assertFalse(cert['calculation_verified'])

    def test_whole_moving_suite_and_comparator_are_retained(self):
        import nikke_gpu
        old=nikke_gpu.SUITES['moving-frames'];new=nikke_gpu.SUITES['moving-visited']
        for key in ('script','source','inputs','native','output_words'):
            self.assertEqual(new[key],old[key])
        self.assertEqual((new['inputs'],new['native']),(15,3))
        self.assertNotEqual(new['golden'],old['golden'])

if __name__=='__main__':unittest.main()
