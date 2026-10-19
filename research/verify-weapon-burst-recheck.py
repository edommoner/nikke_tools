"""Audit saved real-GPU output; never supply CPU observations to GPU input.

Run verify-portable-combat.py first, then pass its report with --report.
This adds full native controller comparisons for seven older authored cases.
The production implementation and fixtures remain shared by CUDA and Metal.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ('app', 'scripts')]
spec = importlib.util.spec_from_file_location('combat_verifier', ROOT / 'scripts/verify-portable-combat.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
from portable_burst_oracle import observe

NATIVE_CASES = {
    'reentry-b1-request-1', 'reentry-b1-request-2',
    'reentry-waits-own-cooldown-and-entry-notice',
    'zero-valued-b3-reentry-state', 'startup-pending-reentry-consumed-once',
    'expired-reentry-state-does-not-open-slot', 'all-stage-state-uses-current-stage',
}


def differences(actual, expected, path=''):
    """Keep every raw observer discrepancy, without changing acceptance values."""
    if isinstance(expected, dict):
        return sum((differences(actual[k], v, path + '.' + k) for k, v in expected.items()), [])
    if isinstance(expected, list):
        assert len(actual) == len(expected), path
        return sum((differences(a, b, path + f'[{i}]') for i, (a, b) in enumerate(zip(actual, expected))), [])
    return [] if actual == expected else [dict(path=path, gpu=actual, raw_cpu=expected)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, default=ROOT / 'research/portable-combat-metal.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'research/portable-weapon-burst-recheck.json')
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    baseline = json.loads(args.baseline.read_text())
    assert report['passed'] and report['gpu_execution_verified']
    assert report['transport']['command_status'] == 'completed'
    assert report['cpu_trace_used_as_gpu_input'] is False
    keys = ['source_sha256', 'input_sha256', 'output_sha256', 'validation_sha256',
            'actual_statuses', 'expected_statuses', 'batch_layout', 'rejected_cases',
            'results', 'cases', 'known_cpu_differences', 'known_health_cpu_differences',
            'known_mode_cpu_differences']
    keys += sorted(k for k in baseline if k.endswith('_cpu_regressions'))
    comparisons = {k: report[k] == baseline[k] for k in keys}
    assert all(comparisons.values()), comparisons
    for key in ('source_sha256', 'validation_sha256'):
        for name, digest in report[key].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    cases = verifier.fixtures()
    assert len(cases) == len(report['results']) == len(report['cases'])
    selected = json.loads((ROOT / 'tests/fixtures/portable-combat-extensions.json').read_text())['cases']
    selected_names = {c['name'] for c in selected}
    rows = []
    raw_mode_audit = []
    for case, gpu, status in zip(cases, report['results'], report['cases']):
        assert status['name'] == case['name'] and status['passed']
        if case['name'] not in selected_names:
            continue
        verifier.contains(gpu['queries'], case['expected_queries'], case['name'] + '.hand')
        row = dict(name=case['name'], passed=True)
        if case['name'] in NATIVE_CASES:
            native = observe(case)
            assert len(native['queries']) == len(gpu['queries'])
            verifier.contains(gpu['queries'], native['queries'], case['name'] + '.native')
            row['native'] = native
        if case['name'].startswith(('mode-', 'finite-', 'reload-', 'charge-')):
            observer_case = copy.deepcopy(case)
            observer_case['mode_session_reference'] = True
            native = observe(observer_case)
            diffs = differences(gpu['queries'], native['queries'])
            raw_mode_audit.append(dict(name=case['name'], raw_cpu_equal=not diffs,
                                       differences=diffs,
                                       declared_contract_difference=bool(case.get('known_mode_cpu_difference'))))
        rows.append(row)
    assert len(rows) == len(selected) == 23
    assert {r['name'] for r in rows if 'native' in r} == NATIVE_CASES
    result = dict(passed=True, fixed_commit='76e0c08aea7185ca00091a7a2efccdbda32181bb',
                  backend=report['backend'], transport=report['transport'],
                  gpu_execution_verified=True, cpu_trace_used_as_gpu_input=False,
                  report_sha256=hashlib.sha256(args.report.read_bytes()).hexdigest(),
                  baseline_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
                  input_sha256=report['input_sha256'], output_sha256=report['output_sha256'],
                  source_sha256=report['source_sha256'], validation_sha256=report['validation_sha256'],
                  previous_full_readback_comparison=comparisons,
                  positives=len(cases), rejections=len(report['rejected_cases']), cases=rows,
                  native_controller_cases=len(NATIVE_CASES),
                  existing_native_regression_counts={k: len(report[k]) for k in keys if k.endswith('_cpu_regressions')},
                  known_mode_cpu_differences=report['known_mode_cpu_differences'],
                  exploratory_raw_mode_audit=raw_mode_audit,
                  exploratory_raw_mode_audit_scope='Unqualified native controller observer projection on older mode fixtures. Discrepancies remain for investigation; not counted as raw CPU equality or resolved by changing fixture expectations.',
                  scope='Component recheck; preserves existing declared CPU differences. No new production behavior or full character certification.',
                  normal_ui_backend='cpu', full_character_certification=0)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(passed=True, authored_cases=len(rows), native_controller_cases=len(NATIVE_CASES))))


if __name__ == '__main__':
    main()
