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
from portable_geometry_oracle import compare, observe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=['metal', 'cuda'], default='metal')
    parser.add_argument('--native-only', action='store_true')
    parser.add_argument('--replay', type=Path, help='CPU-only validation against retained identical input/GPU source')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('core', ROOT / 'scripts/verify-portable-combat.py')
    core = importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    cases = json.loads((ROOT / 'tests/fixtures/portable-geometry.json').read_text())['cases']
    programs = [core.compile_case(c) for c in cases]
    original = portable_runtime.dispatch_programs
    captured = {}
    def dispatch(programs, **kwargs):
        if args.replay:
            prior=json.loads((args.replay/'receipt.json').read_text())
            evidence=prior['evidence']
            assert portable_runtime.pack_programs(programs)==(args.replay/'input.bin').read_bytes()
            for path,digest in evidence['source_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
            assert evidence['backend']==args.backend and evidence['gpu_execution_verified']
            raw=(args.replay/'readback.bin').read_bytes()
            assert hashlib.sha256(raw).hexdigest()==evidence['output_sha256']
        else:
            raw, evidence = original(programs, **kwargs)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        directory = ROOT / 'research/portable-build' / ('geometry-component-' + stamp)
        directory.mkdir(parents=True)
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
            if 'expected_marker' in case:
                owner=case.get('owners',[0])[-1]
                assert native['queries'][-1]['attack_buffs'][owner]==case['expected_marker'],case['name']
            if 'expected_success_events' in case:
                assert [i + 1 for i, row in enumerate(native['attempts']) if row['passed']] == case['expected_success_events'], case['name']
        except AssertionError as error:
            rows.append(dict(name=case['name'], passed=False, error=str(error), native=observe(case), actual=gpu['results'][index] if gpu else None))
        else:
            rows.append(dict(name=case['name'], passed=True, native=native))
    files = ['app/portable_geometry_specs.py', 'app/portable_damage_specs.py', 'app/portable_trigger_specs.py', 'app/portable_specs.py',
             'app/portable_runtime.py', 'scripts/portable_geometry_oracle.py',
             'tests/fixtures/portable-geometry.json', 'research/verify-geometry.py', 'scripts/portable_weapon_oracle.py']
    result = dict(gpu_execution_reused=bool(args.replay),replay_source=str(args.replay) if args.replay else None,passed=all(row['passed'] for row in rows), cases=rows, captured=captured, cpu_trace_used_as_gpu_input=False,
                  validation_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files})
    if gpu is not None:
        result.update({k: v for k, v in gpu.items() if k != 'results'})
    suffix = 'native' if args.native_only else args.backend
    (ROOT / f'research/portable-geometry-{suffix}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    assert result['passed'], [(row['name'], row.get('error')) for row in rows if not row['passed']]
    print(len(cases), 'geometry cases passed', suffix)


if __name__ == '__main__':
    main()
