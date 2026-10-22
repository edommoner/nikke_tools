"""Original full-profile cover, camera and focus consumers through the shared CLI."""
import array
import importlib.util
import sys
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'state_focus_real_base', ROOT/'research/verify-world-roster-regression-short.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
suite, cross = base.suite, base.cross
from portable_state_focus_roster_cases import fixtures
from world_late_attack_random_native import capture_queries
from portable_ordered_history import verify_history,friendly_records
from portable_revival_specs import RNG


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


def native_reference(domain):
    case=domain[0]
    with capture_queries(case['body']['squad'],with_selectors=True) as (_,samples):
        native,trace=base.real.native_reference(case['body'])
    return dict(battle=native,skill_trace=trace,friendly_samples=samples)


def compare(block,domain):
    assert block[0]==0,(domain[0]['name'],'GPU status',block[0])
    expected=native_reference(domain)
    case,prepared,words,metadata=domain
    _,_,_,differences=base.real.compare(block,prepared,(words,metadata),expected['battle'],expected['skill_trace'])
    assert not differences,(case['name'],'full original battle',differences[:8])
    samples=expected['friendly_samples'];verify_history(block,friendly_records(samples))
    if samples:
        state=(3,tuple(block[RNG+8:RNG+632])+(block[RNG],),None)
        digest=hashlib.sha256(json.dumps(state,separators=(',',':')).encode()).hexdigest()
        assert digest==samples[-1]['after_sha256'],(case['name'],'full final MT state')
    return expected
