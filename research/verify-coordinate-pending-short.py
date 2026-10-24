"""Retain all area52 bytes and connect the existing body-only pending queue."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('coordinate_pending_parent',ROOT/'research/verify-coordinate-area-short.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_coordinate_pending_cases import fixtures
SOURCE='gpu/world_coordinate_pending_entry.slang'
INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case
native_reference=parent.native_reference;compare=parent.compare


def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case)
        entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


validate_rejection=parent.validate_rejection
