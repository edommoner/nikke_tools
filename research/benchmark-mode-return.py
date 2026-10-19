"""Compare equivalent placement of the base-return guard after all gates finish.

Production stays fixed. Neither a passing microbenchmark nor byte parity alone
authorizes replacing the verified implementation.
"""
import argparse
import array
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ('app', 'scripts')]
from portable_backend import execute, source_hashes
from portable_runtime import pack_programs
from portable_specs import LIMITS as L

SOURCE = 'a7f478452f7d9c3dbdca97879a2efdf8634c38a9'
P = ROOT / 'research'
BLOCK = '''    if (index < 0 && s.physicalModeIndex[who] == -2)
    {
        s.physicalModeIndex[who] = -1;
        s.nextShot[who] = when;
    }
'''


def prepare(variant):
    folder = P / 'portable-build' / ('mode-return-' + variant)
    folder.mkdir(parents=True, exist_ok=True)
    raw = subprocess.check_output(['git', 'archive', SOURCE, 'gpu'], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(folder, filter='data')
    if variant == 'nested':
        path = folder / 'gpu/combat_runtime.slang'
        text = path.read_text()
        assert text.count(BLOCK) == 1
        text = text.replace(BLOCK, '')
        old = '    else w.capacity = fullCapacity(s,who,s.capacity[who],true,when);'
        assert text.count(old) == 1
        text = text.replace(old, '''    else
    {
        if (s.physicalModeIndex[who] == -2)
        {
            s.physicalModeIndex[who] = -1;
            s.nextShot[who] = when;
        }
        w.capacity = fullCapacity(s,who,s.capacity[who],true,when);
    }''')
        path.write_text(text, newline='\n')
    source = folder / 'mode_return.slang'
    source.write_text('#include "gpu/event_runtime.slang"\n')
    return source.relative_to(ROOT).as_posix()


def run(source, programs):
    raw, evidence = execute(source, 'portableEvents', pack_programs(programs), L['INPUT_WORDS'], L['OUTPUT_WORDS'], 'metal')
    words = array.array('I')
    words.frombytes(raw)
    if sys.byteorder != 'little':
        words.byteswap()
    assert all(words[i * L['OUTPUT_WORDS']] == 0 for i in range(len(programs)))
    return raw, evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', required=True, choices=('parity', 'timing'))
    args = parser.parse_args()
    gates = json.loads((P / 'portable-mode-return-global-gates.json').read_text())
    order = json.loads((P / 'portable-mode-return-timing-order.json').read_text())
    assert gates['passed'] and gates['complete']
    assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes']
    original = source_hashes('gpu/event_runtime.slang')
    spec = importlib.util.spec_from_file_location('mode_cases', ROOT / 'scripts/verify-portable-combat.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    sources = {v: prepare(v) for v in ('separate', 'nested')}
    if args.phase == 'parity':
        programs = [verifier.compile_case(c) for c in verifier.fixtures()]
        rows = {}
        baseline = None
        for variant, source in sources.items():
            raw, evidence = run(source, programs)
            if baseline is None:
                baseline = raw
            assert raw == baseline
            assert evidence['output_sha256'] == hashlib.sha256(raw).hexdigest()
            rows[variant] = evidence
        report = dict(passed=True, inputs=len(programs), all_output_words_equal=True, variants=rows)
    else:
        parity = json.loads((P / 'portable-mode-return-parity.json').read_text())
        assert parity['passed'] and parity['production_source_sha256'] == original
        names = ['mode-round-limit-restores-magazine', 'mode-duration-restores-base']
        workloads = {}
        for name in names:
            case = copy.deepcopy(next(c for c in verifier.fixtures() if c['name'] == name))
            case['combat']['trace'] = 'summary'
            case['script'] = [[3, 24, 0, 0, 0, -1, 0, 0], [3, 2, 0, 0, -1, 0, 0, 0]]
            programs = [verifier.compile_case(case)] * 64
            rows = {v: [] for v in sources}
            expected = None
            for sample in range(4):
                for variant, source in sources.items():
                    raw, evidence = run(source, programs)
                    digest = hashlib.sha256(raw).hexdigest()
                    if expected is None:
                        expected = digest
                    assert digest == expected
                    assert evidence['output_sha256'] == digest
                    rows[variant].append(dict(warmup=sample == 0, **evidence))
                    print(name, sample, variant, evidence['transport']['gpu_seconds'], flush=True)
            medians = {v: statistics.median(r['transport']['gpu_seconds'] for r in values[1:]) for v, values in rows.items()}
            workloads[name] = dict(median_gpu_seconds=medians, nested_to_separate_ratio=medians['nested'] / medians['separate'], samples=rows)
        report = dict(passed=True, workloads=workloads, production_change_adopted=False,
                      scope='64 identical mechanical inputs, 3 seconds, one warmup and three sequential samples per variant; desktop GPU activity is not excluded.')
    assert source_hashes('gpu/event_runtime.slang') == original
    report.update(source_commit=SOURCE, production_source_sha256=original, timing_order=order)
    (P / ('portable-mode-return-' + ('parity' if args.phase == 'parity' else 'benchmark') + '.json')).write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
