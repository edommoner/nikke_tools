"""Common-policy matrix inputs into the unchanged shared Geometry-cache executor."""
import array
import importlib.util
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'research')]
s = importlib.util.spec_from_file_location('matrix_cache_parent', ROOT/'research/verify-coordinate-cache-short.py')
parent = importlib.util.module_from_spec(s)
s.loader.exec_module(parent)
from portable_coordinate_matrix_specs import PROFILE, lower, compiler_policy
from portable_coordinate_matrix_cases import fixtures
from world_coordinate_matrix_common import common_policy

SOURCE = parent.SOURCE
INPUT_WORDS = parent.INPUT_WORDS
OUTPUT_WORDS = parent.OUTPUT_WORDS
STRICT_WIRE_DIMENSIONS = True
suite = parent.suite
cross = parent.cross
validate_rejection = parent.validate_rejection


def compile_case(case):
    with compiler_policy():
        words, meta, bindings, descriptors = parent.compile_case(case)
    return lower(words, descriptors, base_input=107592), meta, bindings, descriptors


def prepare():
    with compiler_policy():
        old, _ = parent.prepare()
    entries = []
    for name, words, domain in old:
        if domain is not None:
            words = lower(words, domain[3], base_input=107592)
        entries.append((name, words, domain))
    for case in fixtures():
        words, meta, bindings, desc = compile_case(case)
        entries.append((case['name'], words, (case, meta, bindings, desc)))
    raw = array.array('I', [len(entries)])
    for _, words, _ in entries:
        raw.extend(words)
    if sys.byteorder != 'little':
        raw.byteswap()
    return entries, raw.tobytes()


def native_reference(domain):
    with common_policy():
        result = parent.native_reference(domain)
    return dict(result, area_matrix_policy=PROFILE)


def compare(block, domain):
    with common_policy():
        result = parent.compare(block, domain)
    return dict(result, area_matrix_policy=PROFILE)
