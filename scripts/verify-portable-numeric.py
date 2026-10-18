"""Binary64 arithmetic experiment. Independent exact-rational oracle, shared
input/comparison, integer-only Slang arithmetic, thin Metal transport. Not a
game simulation and not evidence of production-runtime equivalence.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
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


def cases(random_count=1024):
    fixture = json.loads((ROOT/'tests/fixtures/portable-numeric.json').read_text())
    result = []
    for row in fixture['cases']:
        op, a, b, answer = row['op'], int(row['a'], 16), int(row['b'], 16), int(row['expected'], 16)
        assert answer == expected(op, a, b), row['name']
        result.append((row['name'], op, a, b, answer))
    edges = [0, SIGN, 1, SIGN | 1, (1 << 52)-1, 1 << 52,
             bits(1.0), bits(-1.0), bits(0.1), bits(1/60), bits(1e-9),
             bits(100.0), bits(100.0)-1, INF-1, INF, SIGN | INF, NAN]
    for op in (1, 2, 3, 4, 5, 6):
        for a in edges:
            for b in edges:
                result.append(('edge', op, a, b, expected(op, a, b)))
    rng = random.Random(fixture['seed'])
    for op in (1, 2, 3, 4, 5, 6):
        for _ in range(random_count):
            a, b = rng.getrandbits(64), rng.getrandbits(64)
            result.append(('random-bits', op, a, b, expected(op, a, b)))
        # Closely spaced magnitudes exercise cancellation and half-ULP ties.
        for _ in range(random_count):
            exponent = rng.randrange(1, 2047)
            a = (exponent << 52) | rng.getrandbits(52)
            b = (exponent << 52) | rng.getrandbits(52) | rng.choice([0, SIGN])
            result.append(('close-magnitudes', op, a, b, expected(op, a, b)))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--random-count', type=int, default=1024)
    args = parser.parse_args()
    if not 0 <= args.random_count <= 5000:
        parser.error('random-count must be 0..5000')
    inputs = cases(args.random_count)
    directory = ROOT/'research/portable-build'
    directory.mkdir(parents=True, exist_ok=True)
    sources = ['gpu/binary64.slang', 'gpu/numeric_probe.slang', 'tests/fixtures/portable-numeric.json',
               'scripts/verify-portable-numeric.py', 'scripts/run-metal-probe.swift']
    hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
    report = dict(passed=True, production_runtime_connected=False, gpu_execution_verified=False,
                  stage='fixture-validation' if args.validate_only else 'gpu-execution',
                  scope='Binary64 arithmetic/comparison candidate only; no pow, conversions, game state, or production performance validation.',
                  source_sha256=hashes, cases=len(inputs),
                  groups=dict(Counter(row[0] for row in inputs)),
                  rounding='nearest-ties-to-even', oracle='exact rational, rounded once to binary64',
                  random_count_per_operation_per_group=args.random_count)
    path = ROOT/('research/portable-numeric-fixtures.json' if args.validate_only else 'research/portable-numeric-metal.json')
    if not args.validate_only:
        # A failed compiler/driver run must not leave an older success report.
        path.write_text(json.dumps({**report, 'passed': False, 'stage': 'execution-pending'}, indent=2)+'\n')
        if sys.platform != 'darwin':
            parser.error('Metal execution requires macOS; CPU fallback is not GPU verification')
        compiler = ROOT/f'.tools/slang-2026.20-{platform.system()}-{platform.machine()}/bin/slangc'
        generated = {}
        for target, suffix in [('cuda', 'cu'), ('metal', 'metal')]:
            process = subprocess.run([str(compiler), str(ROOT/'gpu/numeric_probe.slang'), '-entry', 'numericProbe',
                                      '-target', target, '-fp-mode', 'precise'], capture_output=True)
            if process.returncode:
                sys.stderr.write(process.stderr.decode()); raise SystemExit(process.returncode)
            shader_path = directory/f'numeric_probe.{suffix}'
            shader_path.write_bytes(process.stdout)
            generated[target] = hashlib.sha256(process.stdout).hexdigest()
        words = [len(inputs)]
        for _, op, a, b, _ in inputs:
            words += [op, a & 0xffffffff, a >> 32, b & 0xffffffff, b >> 32]
        input_path, output_path = directory/'numeric-input.bin', directory/'numeric-output.bin'
        packed = struct.pack('<'+'I'*len(words), *words)
        input_path.write_bytes(packed)
        output_path.unlink(missing_ok=True)
        process = subprocess.run(['swift', str(ROOT/'scripts/run-metal-probe.swift'),
                                  str(directory/'numeric_probe.metal'), str(input_path), str(output_path),
                                  'numericProbe', '5', '2'], capture_output=True, text=True)
        if process.returncode:
            sys.stderr.write(process.stderr or process.stdout); raise SystemExit(process.returncode)
        actual = struct.unpack('<'+'Q'*len(inputs), output_path.read_bytes())
        mismatches = []
        for index, (row, got) in enumerate(zip(inputs, actual)):
            if row[4] != got:
                mismatches.append(dict(index=index, group=row[0], op=row[1], a=f'{row[2]:016x}',
                                       b=f'{row[3]:016x}', expected=f'{row[4]:016x}', actual=f'{got:016x}'))
        report.update(passed=not mismatches, gpu_execution_verified=True,
                      backend='metal', transport=json.loads(process.stdout),
                      outputs_sha256=generated, input_sha256=hashlib.sha256(packed).hexdigest(),
                      output_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
                      mismatch_count=len(mismatches), mismatches=mismatches[:20])
    assert hashes == {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
