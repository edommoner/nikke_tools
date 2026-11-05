"""Wire and comparison boundaries for the complete moving-frame profile."""
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'scripts')]

class MovingFramesTests(unittest.TestCase):
    pass

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
