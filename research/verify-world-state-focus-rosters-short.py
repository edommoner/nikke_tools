"""Original full-profile cover, camera and focus consumers through the shared CLI."""
import array
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'state_focus_real_base', ROOT/'research/verify-world-roster-regression-short.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
suite, cross = base.suite, base.cross
from portable_state_focus_roster_cases import fixtures


def prepare():
    entries = []
    for case in fixtures():
        prepared = base.real.engine_worker.evaluate(dict(case['body'], _portable_static_inputs=True))
        words, metadata = base.real.compile_projectile_battle(prepared)
        entries.append((case['name'], words, (case, prepared, words, metadata)))
    packed = array.array('I', [len(entries)])
    for _, words, _ in entries:
        packed.extend(words)
    if sys.byteorder != 'little':
        packed.byteswap()
    return entries, packed.tobytes()


compare = base.compare
