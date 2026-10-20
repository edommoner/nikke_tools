"""Capture exact current-core parity before the unchanged native/old-core guards.

Uses the committed CUDA-matching baseline, without needing its large local raw
file. A mismatch preserves the full readback and fails without retrying GPU work.
"""
import array
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '80170c3b922b666eadb1f72bec22331c183a89b4'
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
import portable_runtime as runtime
from portable_specs import LIMITS


def main():
    manifest = json.loads(subprocess.check_output([
        'git', 'show', BASELINE + ':research/portable-element-baseline-output-blocks.json'
    ], cwd=ROOT))
    assert manifest['passed'] and manifest['programs'] == 2182
    assert manifest['output_words'] == LIMITS['OUTPUT_WORDS']
    original = runtime.dispatch_programs
    calls = 0

    def captured(programs, **kwargs):
        nonlocal calls
        calls += 1
        assert calls == 1 and len(programs) == manifest['programs']
        raw, evidence = original(programs, **kwargs)
        stride = LIMITS['OUTPUT_WORDS'] * 4
        changed = []
        actual_blocks = []
        for block in manifest['blocks']:
            index = block['index']
            view = memoryview(raw)[index * stride:(index + 1) * stride]
            digest = hashlib.sha256(view).hexdigest()
            actual_blocks.append(digest)
            if digest != block['sha256']:
                changed.append(dict(**block, actual_sha256=digest))
        input_equal = evidence['input_sha256'] == manifest['input_sha256']
        output_equal = hashlib.sha256(raw).hexdigest() == manifest['output_sha256']
        passed = input_equal and output_equal and not changed
        backend = kwargs.get('backend', 'metal')
        receipt = dict(
            passed=passed, baseline_proof_commit=BASELINE,
            source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            stage='full-readback-before-original-guards-and-native-comparisons',
            programs=len(programs), input_equal=input_equal, output_equal=output_equal,
            baseline_input_sha256=manifest['input_sha256'],
            baseline_output_sha256=manifest['output_sha256'],
            actual_block_sha256=actual_blocks, changed=changed, evidence=evidence,
            capture_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            no_gpu_retry=True, no_output_normalization=True,
            initial_metal_finding_open=True, root_cause_resolved=False,
        )
        if not passed:
            directory = ROOT / 'research/portable-build' / ('element-optimized-failure-' + backend)
            directory.mkdir(parents=True, exist_ok=True)
            raw_path = directory / 'readback.bin'
            raw_path.write_bytes(raw)
            receipt['failed_raw_path'] = str(raw_path)
            for block in changed:
                index = block['index']
                words = array.array('I', programs[index][0])
                if sys.byteorder != 'little':
                    words.byteswap()
                (directory / f'program-{index}.bin').write_bytes(words.tobytes())
                (directory / f'output-{index}.bin').write_bytes(raw[index * stride:(index + 1) * stride])
        path = ROOT / 'research' / f'portable-element-optimized-{backend}-readback.json'
        path.write_text(json.dumps(receipt, indent=2) + '\n')
        assert passed, f'Exact baseline comparison failed; evidence retained at {path}'
        return raw, evidence

    runtime.dispatch_programs = captured
    spec = importlib.util.spec_from_file_location('strict_element_driver', ROOT / 'research/verify-element-regression.py')
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    try:
        driver.main()
        assert calls == 1
    finally:
        runtime.dispatch_programs = original


if __name__ == '__main__':
    main()
