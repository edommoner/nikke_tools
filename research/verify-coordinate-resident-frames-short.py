"""Complete original106 inputs and comparators; resource-backed Frame storage."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('resident_frames_parent',ROOT/'research/verify-coordinate-resident-arc-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
SOURCE='gpu/world_coordinate_resident_frames_entry.slang'
suite=parent.suite;cross=parent.cross;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
prepare=parent.prepare;native_reference=parent.native_reference;compare=parent.compare
native_comparison_adapter=parent.native_comparison_adapter;validate_rejection=parent.validate_rejection
