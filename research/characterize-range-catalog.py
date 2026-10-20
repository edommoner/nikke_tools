"""Native binary64 range endpoint corpus across all203 original/mode weapons.

This is CPU geometry evidence,not GPU admission or character certification.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'scripts')]
import engine_worker
from calculator.buff_manager import optimal_range_of, in_optimal_range, _NIKKE


def main():
    audit = json.loads((ROOT/'research/portable-catalog-readiness.json').read_text())
    names = [c['character'] for c in audit['characters']]
    assert len(names) == 203 and len(set(names)) == 203
    digest = hashlib.sha256()
    cases = 0
    rows = []
    for name in names:
        assert name in _NIKKE
        for weapon in ('AR', 'SMG', 'SG', 'SR', 'RL', 'MG'):
            lo, hi = optimal_range_of(name, weapon)
            assert math.isfinite(lo) and math.isfinite(hi) and 0 <= lo <= hi
            counts = dict(endpoint=0, membership=0)
            for minimum, maximum in [(0, 0), (50, 20), (100, 100), (150, 20)]:
                buffs = dict(optimal_range_min_pct=minimum, optimal_range_max_pct=maximum)
                lower = max(0., lo*(1.-minimum/100.)) - 1e-9
                upper = hi*(1.+maximum/100.) + 1e-9
                for distance, expected in [(math.nextafter(lower, -math.inf), False), (lower, True),
                        (math.nextafter(lower, math.inf), True), (math.nextafter(upper, -math.inf), True),
                        (upper, True), (math.nextafter(upper, math.inf), False)]:
                    actual = in_optimal_range(dict(distance=distance), name, weapon, buffs)
                    assert actual == expected, (name, weapon, minimum, maximum, distance)
                    record = [name, weapon, lo, hi, minimum, maximum, distance.hex(), actual]
                    digest.update(json.dumps(record, ensure_ascii=False, separators=(',', ':')).encode()+b'\n')
                    cases += 1
                    counts['endpoint'] += 1
            for weapons, expected in [([], False), ([weapon], True), ([w for w in ('AR','SMG','SG','SR','RL','MG') if w != weapon], False)]:
                actual = in_optimal_range(dict(optimal_range_weapons=weapons), name, weapon, {})
                assert actual == expected
                digest.update(json.dumps([name, weapon, weapons, actual], ensure_ascii=False, separators=(',', ':')).encode()+b'\n')
                cases += 1
                counts['membership'] += 1
            rows.append(dict(character=name, weapon=weapon, original_weapon=_NIKKE[name]['weapon_type'],
                             lower=lo, upper=hi, **counts))
    files = ['research/characterize-range-catalog.py', 'research/portable-catalog-readiness.json',
             'app/engine_worker.py', 'app/engine_compat.py',
             'research/upstream/nikke-calc-master/calculator/buff_manager.py',
             'research/upstream/nikke-calc-master/data/parsed_nikke.json']
    report = dict(passed=True, cpu_only=True, gpu_execution_performed=False, gpu_admission_enabled=False,
        characters=203, weapon_contexts=1218, native_cases=cases, native_corpus_sha256=digest.hexdigest(),
        rows=rows, full_character_verified=0,
        rules=['Each binary64 slack endpoint is included;adjacent representable value outside is excluded',
               'Minimum buffs100/150 percent clamp lower bound at0 before subtracting slack',
               'No distance:explicit weapon membership;not an estimate from a distance',
               'Original and all six active-mode range tables use the native resolver'],
        scope='CPU helper domain includes near-zero negative distance endpoint probes;real-input validation remains separate',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
    (ROOT/'research/portable-range-catalog-native.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Native203-character range contexts1218,cases', cases, 'verified;GPU admission remains disabled')


if __name__ == '__main__':
    main()
