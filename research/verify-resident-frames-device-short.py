"""Bounded device connection using the independently sealed full Frame source."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prefix=module('frame_device_prefix','research/verify-coordinate-resident-device-short.py')
full=module('frame_device_full','research/verify-coordinate-resident-frames-short.py')
SOURCE=full.SOURCE;suite=full.suite;cross=full.cross;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=full.NATIVE_COMPARISON_CONTEXT
# The existing prefix guard checks all words, order and non-null native domains.
prepare=prefix.prepare
native_reference=full.native_reference;compare=full.compare
native_comparison_adapter=full.native_comparison_adapter;validate_rejection=full.validate_rejection
