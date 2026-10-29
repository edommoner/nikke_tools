"""Complete moving-group contract with shared resource-backed dispatch frames."""
import importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'research')]
spec = importlib.util.spec_from_file_location('moving_frames_parent', ROOT / 'research/verify-moving-group.py')
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
SOURCE = 'gpu/world_moving_frames_entry.slang'
STRICT_WIRE_DIMENSIONS = True
suite = parent.suite
cross = parent.cross
NATIVE_COMPARISON_CONTEXT = parent.NATIVE_COMPARISON_CONTEXT
prepare = parent.prepare
native_reference = parent.native_reference
compare = parent.compare
validate_rejection = parent.validate_rejection
