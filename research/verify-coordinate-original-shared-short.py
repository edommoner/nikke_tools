"""Same original cover cases/readers under the stable existing-handler entry."""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('original_shared_cover',Path(__file__).with_name('verify-coordinate-original-cover-short.py'));parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
SOURCE='gpu/world_coordinate_original_shared_entry.slang'
INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
prepare=parent.prepare;native_reference=parent.native_reference;compare=parent.compare;validate_rejection=parent.validate_rejection
fixtures=parent.fixtures;prepare_case=parent.prepare_case;compile_coordinate_battle=parent.compile_coordinate_battle
