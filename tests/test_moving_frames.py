"""Wire and comparison boundaries for the complete moving-frame profile."""
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'scripts')]

class MovingFramesTests(unittest.TestCase):
    def test_full_contract_reuses_original_prepare_native_and_compare(self):
        import nikke_gpu
        old = nikke_gpu.SUITES['moving-group-current']
        new = nikke_gpu.SUITES['moving-frames']
        for field in ('inputs', 'native', 'output_words'):
            self.assertEqual(new[field], old[field])
        self.assertEqual((new['inputs'], new['native']), (15, 3))
        spec = importlib.util.spec_from_file_location('moving_frames_test', ROOT / new['script'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in ('prepare', 'native_reference', 'compare', 'validate_rejection'):
            self.assertIs(getattr(module, name), getattr(module.parent, name))
        self.assertTrue(module.STRICT_WIRE_DIMENSIONS)
        self.assertEqual(module.SOURCE, new['source'])
        self.assertNotEqual(new['golden'], old['golden'])

    def test_new_entry_uses_existing_frame_bank_and_exact_moving_wire(self):
        from portable_backend import validate_composed_stride
        from portable_moving_typed_wire import INPUT, OUTPUT
        source = 'gpu/world_moving_frames_entry.slang'
        self.assertEqual((ROOT / source).read_text().splitlines()[1:], [
            '#define PORTABLE_RESIDENT_FRAME_STACK', '#include "world_moving_typed_entry.slang"'])
        validate_composed_stride(source, INPUT, OUTPUT)
        for dimensions in ((INPUT - 1, OUTPUT), (INPUT, OUTPUT - 1), (INPUT, OUTPUT + 1)):
            with self.assertRaises(ValueError):
                validate_composed_stride(source, *dimensions)

    def test_historical_seal_keeps_all_prior_fingerprints_and_reviewed_compiler_source(self):
        import json
        import hashlib
        import nikke_gpu
        from portable_backend import source_hashes
        old = json.loads((ROOT / 'research/portable-moving-group-v2-expected.json').read_text())
        raw = (ROOT / nikke_gpu.SUITES['moving-frames']['golden']).read_bytes()
        new = json.loads(raw)
        for key in ('input_sha256', 'output_sha256', 'entries'):
            self.assertEqual(new[key], old[key])
        sources = source_hashes('gpu/world_moving_frames_entry.slang')
        if 'gpu/quantity_visited.slang' in sources:
            # Exact reviewed inverse only: retain this historical Frame seal,
            # without treating it as a current-source quantity bitset proof.
            delta = json.loads((ROOT / 'tests/fixtures/quantity-visited-source-change-v1.json').read_text())
            name = 'gpu/quantity_runtime.slang'
            row = delta['files'][name]
            source = (ROOT / name).read_text()
            self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), row['after_sha256'])
            self.assertEqual(sources['gpu/quantity_visited.slang'], delta['added_sources']['gpu/quantity_visited.slang'])
            for hunk in reversed(row['hunks']):
                self.assertEqual(source.count(hunk['after']), 1)
                source = source.replace(hunk['after'], hunk['before'], 1)
            self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), row['before_sha256'])
            sources[name] = row['before_sha256']
            del sources['gpu/quantity_visited.slang']
        self.assertEqual(new['source_sha256'], sources)
        cert = json.loads((ROOT / 'research/portable-compiler-full--moving-frames-source-certificate.json').read_text())
        self.assertEqual(cert['baseline_golden_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(cert['source_sha256'], new['source_sha256'])
        self.assertEqual(cert['generated_normalized'], new['generated_normalized'])
        self.assertFalse(cert['calculation_verified'])
        self.assertFalse(nikke_gpu.SUITES['moving-frames']['development_only'])
        cached = nikke_gpu.SUITES['moving-frames-cache-only']
        self.assertEqual(cached['source'], nikke_gpu.SUITES['moving-frames']['source'])
        self.assertTrue(cached['require_paired_generation'])
        self.assertEqual(cached['cuda_cache_profile'], 'compile-cache-only-v1')

# Reuse the generic storage contract, without claiming the unrelated historical
# full106 certificate is current for this moving-group source.
_spec = importlib.util.spec_from_file_location('moving_shared_frame_tests', ROOT / 'tests/test_dispatch_frame_storage.py')
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)
class SharedFrameStorageTests(unittest.TestCase):
    pass
for _name in (
    'test_full_frame_and_generated_storage_match_single_shared_definition',
    'test_signed_argument_nan_payload_and_signed_zero_bits_are_not_float_converted',
    'test_outside_exact_scalar_ranges_or_incomplete_wire_is_rejected',
    'test_probe_checks_all32_slots_and_every_output_word_including_guard_errors',
    'test_common_initializer_and_old_array_variant_remain_available',
    'test_historical_inverse_accepts_only_reviewed_sources_and_retains_all_old_baselines',
):
    setattr(SharedFrameStorageTests, _name, getattr(_shared.DispatchFrameStorageTests, _name))

if __name__ == '__main__':
    unittest.main()
