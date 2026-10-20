"""Verify the measured helper against the completed2280-input both-GPU baseline.

Retain raw input/readback before strict hashes or native assertions;never retry.
"""
import array
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '988858f853594e2a0770640fa21bbd94d7c08cc0'
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
import portable_runtime as runtime
from portable_specs import LIMITS


def main():
    baseline = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':research/portable-combat-metal.json'], cwd=ROOT))
    assert baseline['passed'] and len(baseline['cases']) + len(baseline['rejected_cases']) == 2280
    original = runtime.dispatch_programs
    calls = 0

    def captured(programs, **kwargs):
        nonlocal calls
        calls += 1
        assert calls == 1 and len(programs) == 2280
        backend = kwargs.get('backend', 'metal')
        directory = ROOT / 'research/portable-build' / ('probability-optimized-' + backend + '-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
        directory.mkdir(parents=True)
        with (directory / 'input.bin').open('wb') as stream:
            for words, _ in programs:
                packed = array.array('I', words)
                if sys.byteorder != 'little':
                    packed.byteswap()
                stream.write(packed.tobytes())
        raw, evidence = original(programs, **kwargs)
        (directory / 'readback.bin').write_bytes(raw)
        (directory / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
        with (directory / 'input.bin').open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == evidence['input_sha256']
        assert hashlib.sha256(raw).hexdigest() == evidence['output_sha256']
        passed = all(evidence[k] == baseline[k] for k in ['input_sha256', 'output_sha256'])
        stride = LIMITS['OUTPUT_WORDS'] * 4
        receipt = dict(passed=passed, baseline_proof_commit=BASELINE,
            source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            programs=2280, input_equal=evidence['input_sha256'] == baseline['input_sha256'],
            output_equal=evidence['output_sha256'] == baseline['output_sha256'],
            input_sha256=evidence['input_sha256'], output_sha256=evidence['output_sha256'],
            input_path=str(directory / 'input.bin'), raw_path=str(directory / 'readback.bin'),
            actual_block_sha256=[hashlib.sha256(memoryview(raw)[i*stride:(i+1)*stride]).hexdigest() for i in range(2280)],
            driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), evidence=evidence,
            no_gpu_retry=True, no_output_normalization=True, gpu_execution_reused=False,
            initial_unlocalized_metal_finding_open=True)
        path = ROOT / ('research/portable-probability-optimized-' + backend + '-readback.json')
        path.write_text(json.dumps(receipt, indent=2) + '\n')
        assert passed, f'Baseline mismatch;full input/readback retained at {directory}'
        return raw, evidence

    runtime.dispatch_programs = captured
    spec = importlib.util.spec_from_file_location('strict_probability_driver', ROOT / 'research/verify-probability-regression.py')
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    try:
        driver.main()
        assert calls == 1
    finally:
        runtime.dispatch_programs = original
    backend = 'cuda' if 'cuda' in sys.argv else 'metal'
    report = json.loads((ROOT / ('research/portable-combat-' + backend + '.json')).read_text())
    for key in ['cases', 'rejected_cases', 'actual_statuses', 'expected_statuses'] + [k for k in baseline if k.endswith('_cpu_regressions') or k.startswith('known_')]:
        assert report[key] == baseline[key], key
    print('Measured helper preserves all2280 baseline inputs/output words,decoded cases and native groups')


if __name__ == '__main__':
    main()
