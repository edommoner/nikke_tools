"""Binary64 arithmetic experiment. Independent exact-rational oracle, shared
input/comparison, integer-only Slang arithmetic, thin Metal transport. Not a
game simulation and not evidence of production-runtime equivalence.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
import gmpy2
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from portable_backend import execute
SIGN = 1 << 63
INF = 0x7ff0000000000000
NAN = 0x7ff8000000000000


def bits(value):
    return struct.unpack('<Q', struct.pack('<d', value))[0]


def number(value):
    return struct.unpack('<d', struct.pack('<Q', value))[0]


def expected(op, a, b):
    """One final binary64 rounding of an exact rational result, not float32.
    Exceptional values/signed zero have IEEE-defined explicit handling.
    """
    if op in (7, 8, 12):
        if not math.isfinite(number(a)):
            return 0
        integer = round(number(a)) if op == 7 else math.trunc(number(a)) if op == 8 else math.floor(number(a))
        return integer & (2**64-1) if -2**63 <= integer < 2**63 else 0
    if op == 9:
        if a & ~SIGN >= INF or a & ~SIGN == 0:
            return NAN if a & ~SIGN > INF else a
        return bits(float(math.floor(number(a))))
    if op == 10:
        return bits(float(a if a < SIGN else a-2**64))
    if op == 11:
        x = number(a)
        if not math.isfinite(x) or x < 0:
            return 0
        if x >= 1:
            return bits(1.0)
        if x == 0:
            return 0
        bounds = []
        for direction in (gmpy2.RoundDown, gmpy2.RoundUp):
            with gmpy2.context(precision=256, round=direction):
                value = gmpy2.mpfr(x) ** gmpy2.mpfr(2.55)
            bounds.append(bits(float(value)))
        assert bounds[0] == bounds[1], ('increase MPFR oracle precision', a)
        return bounds[0]
    if op == 13:
        return a & ~SIGN
    if op == 14:
        return int(a & ~SIGN < INF)
    if op in (5, 6):
        return int(number(a) < number(b) if op == 5 else number(a) == number(b))
    if op == 2:
        return expected(1, a, b ^ SIGN)
    ma, mb = a & ~SIGN, b & ~SIGN
    sign = (a ^ b) & SIGN
    if ma > INF or mb > INF:
        return NAN
    if op == 1:
        if ma == INF or mb == INF:
            return NAN if ma == mb and sign else a if ma == INF else b
        exact = Fraction(number(a)) + Fraction(number(b))
        if not exact:
            return SIGN if a == b == SIGN else 0
    elif op == 3:
        if ma == INF or mb == INF:
            return NAN if ma == 0 or mb == 0 else sign | INF
        if ma == 0 or mb == 0:
            return sign
        exact = Fraction(number(a)) * Fraction(number(b))
    else:
        if ma == mb == INF or ma == mb == 0:
            return NAN
        if ma == INF or mb == 0:
            return sign | INF
        if ma == 0 or mb == INF:
            return sign
        exact = Fraction(number(a)) / Fraction(number(b))
    try:
        return bits(float(exact))
    except OverflowError:
        return (SIGN if exact < 0 else 0) | INF


def expected_status(op, a):
    if op in (7, 8, 12):
        x = number(a)
        if not math.isfinite(x):
            return 1
        integer = round(x) if op == 7 else math.trunc(x) if op == 8 else math.floor(x)
        return int(not -2**63 <= integer < 2**63)
    if op == 11:
        return 2 if not math.isfinite(number(a)) or number(a) < 0 else 0
    return 0


def cases(random_count=1024):
    fixture = json.loads((ROOT/'tests/fixtures/portable-numeric.json').read_text())
    result = []
    for row in fixture['cases']:
        op, a, b, answer = row['op'], int(row['a'], 16), int(row['b'], 16), int(row['expected'], 16)
        assert answer == expected(op, a, b), row['name']
        assert row.get('status',0) == expected_status(op,a), row['name']
        result.append((row['name'], op, a, b, answer))
    edges = [0, SIGN, 1, SIGN | 1, (1 << 52)-1, 1 << 52,
             bits(1.0), bits(-1.0), bits(0.1), bits(1/60), bits(1e-9),
             bits(100.0), bits(100.0)-1, bits(0.5), bits(-0.5), bits(1.5), bits(-1.5), bits(2.5), bits(-2.5), bits(2.0**63), bits(-2.0**63), bits(2.0**63)-1, bits(-2.0**63)+1, INF-1, INF, SIGN | INF, NAN]
    for op in range(1, 15):
        for a in edges:
            for b in (edges if op <= 6 else [0]):
                result.append(('edge', op, a, b, expected(op, a, b)))
    rng = random.Random(fixture['seed'])
    for op in range(1, 15):
        for _ in range(random_count):
            a, b = rng.getrandbits(64), rng.getrandbits(64)
            result.append(('random-bits', op, a, b, expected(op, a, b)))
        # Closely spaced magnitudes exercise cancellation and half-ULP ties.
        for _ in range(random_count):
            exponent = rng.randrange(1, 2047)
            a = (exponent << 52) | rng.getrandbits(52)
            b = (exponent << 52) | rng.getrandbits(52) | rng.choice([0, SIGN])
            result.append(('close-magnitudes', op, a, b, expected(op, a, b)))
    # Concentrate pow around 1, underflow/subnormal crossover, and ordinary
    # ratios. These are inputs, never a host-computed intermediate game state.
    for x in [math.nextafter(1.0, 0.0), 0.25, 0.5, 0.9, 0.01] + [2.0**(-i) for i in range(1, 430)] + [rng.random() for _ in range(random_count)]:
        a = bits(x)
        result.append(('pow-domain', 11, a, 0, expected(11, a, 0)))
    # Dense representable inputs on both sides of underflow, normal/subnormal
    # and probability transitions, with an independent MPFR root as the seed.
    for exponent in (-1075,-1022,-53,-1):
        with gmpy2.context(precision=256):
            center=float((gmpy2.mpfr(2)**exponent)**(1/gmpy2.mpfr(2.55)))
        for direction in (0.0,1.0):
            x=center
            for _ in range(16):
                x=math.nextafter(x,direction);a=bits(x)
                result.append(('pow-transition',11,a,0,expected(11,a,0)))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    parser.add_argument('--random-count', type=int, default=1024)
    parser.add_argument('--report-suffix',choices=('short',),help='Keep a short cross-GPU check separate from the full record')
    args = parser.parse_args()
    if not 0 <= args.random_count <= 2000:
        parser.error('random-count must be 0..2000')
    inputs = cases(args.random_count)
    directory = ROOT/'research/portable-build'
    directory.mkdir(parents=True, exist_ok=True)
    sources = ['gpu/binary64.slang', 'gpu/core_probability.slang', 'gpu/numeric_probe.slang', 'tests/fixtures/portable-numeric.json',
               'scripts/verify-portable-numeric.py', 'scripts/run-metal-probe.swift', 'app/portable_backend.py']
    hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
    report = dict(passed=True, production_runtime_connected=False, gpu_execution_verified=False,
                  stage='fixture-validation' if args.validate_only else 'gpu-execution',
                  scope='Binary64 arithmetic, checked int64 conversion, floor and clamped pow(x,binary64(2.55)); no autonomous battle validation.',
                  source_sha256=hashes, validation_sha256=hashes, cases=len(inputs),
                  groups=dict(Counter(row[0] for row in inputs)),
                  rounding='nearest-ties-to-even', oracle='exact rational for arithmetic; integer/range checks; MPFR directed 256-bit bounds for pow', mpfr=gmpy2.mpfr_version(),
                  random_count_per_operation_per_group=args.random_count)
    suffix='-'+args.report_suffix if args.report_suffix else ''
    kind='fixtures' if args.validate_only else args.backend
    path = ROOT/f'research/portable-numeric-{kind}{suffix}.json'
    if not args.validate_only:
        # A failed compiler/driver run must not leave an older success report.
        path.write_text(json.dumps({**report, 'passed': False, 'stage': 'execution-pending'}, indent=2)+'\n')
        words = [len(inputs)]
        for _, op, a, b, _ in inputs:
            words += [op, a & 0xffffffff, a >> 32, b & 0xffffffff, b >> 32]
        packed = struct.pack('<'+'I'*len(words), *words)
        raw_output,evidence = execute('gpu/numeric_probe.slang','numericProbe',packed,5,3,args.backend)
        raw = struct.unpack('<'+'I'*(3*len(inputs)), raw_output)
        actual = [(raw[i*3] | raw[i*3+1]<<32, raw[i*3+2]) for i in range(len(inputs))]
        mismatches = []
        for index, (row, got) in enumerate(zip(inputs, actual)):
            if (row[4], expected_status(row[1], row[2])) != got:
                mismatches.append(dict(index=index, group=row[0], op=row[1], a=f'{row[2]:016x}',
                                       b=f'{row[3]:016x}', expected=f'{row[4]:016x}', actual=f'{got[0]:016x}', expected_status=expected_status(row[1], row[2]), actual_status=got[1]))
        report.update(passed=not mismatches, **evidence,
                      mismatch_count=len(mismatches), mismatches=mismatches[:20])
    assert hashes == {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
