"""Shared component driver for real Metal/CUDA and independent native checks."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
import portable_runtime
from portable_runtime import run_programs
from portable_probability_oracle import compare, observe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=['metal', 'cuda'], default='metal')
    parser.add_argument('--native-only', action='store_true')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('core', ROOT / 'scripts/verify-portable-combat.py')
    core = importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    cases = json.loads((ROOT / 'tests/fixtures/portable-probability.json').read_text())['cases']
    programs = [core.compile_case(c) for c in cases]
    original = portable_runtime.dispatch_programs
    captured = {}
    def dispatch(programs, **kwargs):
        raw, evidence = original(programs, **kwargs)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        directory = ROOT / 'research/portable-build' / ('probability-component-' + stamp)
        directory.mkdir()
        (directory / 'readback.bin').write_bytes(raw)
        (directory / 'input.bin').write_bytes(portable_runtime.pack_programs(programs))
        captured.update(raw_path=str(directory / 'readback.bin'), input_path=str(directory / 'input.bin'), evidence=evidence)
        (directory / 'receipt.json').write_text(json.dumps(captured, indent=2) + '\n')
        return raw, evidence
    portable_runtime.dispatch_programs = dispatch
    try:
        gpu = None if args.native_only else run_programs(programs, backend=args.backend)
    finally:
        portable_runtime.dispatch_programs = original
    rows = []
    for index, case in enumerate(cases):
        try:
            native = observe(case) if gpu is None else compare(case, gpu['results'][index], core.contains)
            if 'expected_success_events' in case:
                assert [i + 1 for i, row in enumerate(native['attempts']) if row['passed']] == case['expected_success_events'], case['name']
        except AssertionError as error:
            rows.append(dict(name=case['name'], passed=False, error=str(error), native=observe(case), actual=gpu['results'][index] if gpu else None))
        else:
            rows.append(dict(name=case['name'], passed=True, native=native))
    files = ['app/portable_probability_specs.py', 'app/portable_trigger_specs.py', 'app/portable_specs.py',
             'app/portable_runtime.py', 'scripts/portable_probability_oracle.py',
             'tests/fixtures/portable-probability.json', 'research/verify-probability.py']
    result = dict(passed=all(row['passed'] for row in rows), cases=rows, captured=captured, cpu_trace_used_as_gpu_input=False,
                  validation_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files})
    if gpu is not None:
        result.update({k: v for k, v in gpu.items() if k != 'results'})
    suffix = 'native' if args.native_only else args.backend
    (ROOT / f'research/portable-probability-{suffix}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    assert result['passed'], [(row['name'], row.get('error')) for row in rows if not row['passed']]
    print(len(cases), 'probability cases passed', suffix)


if __name__ == '__main__':
    main()
