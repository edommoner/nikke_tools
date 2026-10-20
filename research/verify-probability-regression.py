"""Full common verifier with exact2182 prior input/readback preservation.

Retains all current input/output bytes before checking hashes or CPU results.
No GPU retry, relaxed guard, tolerance, or prior-output normalization.
"""
import argparse
import array
import datetime
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIOR = 'f2206ef4a32fb89ad9c4f2381bb9dbfa5ec711d1'
BLOCK_PROOF = '80170c3b922b666eadb1f72bec22331c183a89b4'
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
import portable_runtime as runtime
from portable_specs import ABI, LIMITS


def old_report(path):
    return json.loads(subprocess.check_output(['git', 'show', PRIOR + ':' + path], cwd=ROOT))


def packed_words(words):
    packed = array.array('I', words)
    if sys.byteorder != 'little':
        packed.byteswap()
    return packed.tobytes()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=['metal', 'cuda'], default='metal')
    parser.add_argument('--batch-size', type=int)
    parser.add_argument('--replay', type=Path, help='CPU-only verifier replay of retained,source/input-identical GPU bytes')
    args = parser.parse_args()
    prior = old_report('research/portable-combat-metal.json')
    manifest = json.loads(subprocess.check_output(['git', 'show', BLOCK_PROOF + ':research/portable-element-baseline-output-blocks.json'], cwd=ROOT))
    assert prior['passed'] and manifest['passed'] and manifest['output_sha256'] == prior['output_sha256']
    spec = importlib.util.spec_from_file_location('probability_core', ROOT / 'scripts/verify-portable-combat.py')
    verifier = importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    cases = verifier.fixtures()
    assert [c['name'] for c in cases[:len(prior['cases'])]] == [c['name'] for c in prior['cases']]
    indices = list(range(len(prior['cases']))) + list(range(len(cases), len(cases) + len(prior['rejected_cases'])))
    assert len(indices) == 2182 and ABI == 0x5045566C
    original = runtime.dispatch_programs
    calls = 0
    projection = None

    def captured(programs, **kwargs):
        nonlocal calls, projection
        calls += 1
        assert calls == 1
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        directory = ROOT / 'research/portable-build' / ('probability-core-' + stamp)
        directory.mkdir(parents=True)
        with (directory / 'input.bin').open('wb') as stream:
            stream.write(struct.pack('<I', len(programs)))
            for words, _ in programs:
                stream.write(packed_words(words))
        digest = hashlib.sha256(struct.pack('<I', len(indices)))
        for index in indices:
            words = list(programs[index][0]);assert words[0] == ABI
            words[0] = 0x5045566B
            digest.update(packed_words(words))
        assert digest.hexdigest() == prior['input_sha256'], f'Previous inputs changed; current input retained at {directory}'
        if args.replay:
            assert file_sha(directory / 'input.bin') == file_sha(args.replay / 'input.bin'), 'Replay input must be byte-identical'
            evidence = json.loads((args.replay / 'evidence.json').read_text())
            assert evidence['backend'] == args.backend and evidence['gpu_execution_verified']
            for path, expected in evidence['source_sha256'].items():
                assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
            assert file_sha(directory / 'input.bin') == evidence['input_sha256']
            raw = (args.replay / 'readback.bin').read_bytes()
            assert hashlib.sha256(raw).hexdigest() == evidence['output_sha256']
        else:
            raw, evidence = original(programs, **kwargs)
        (directory / 'readback.bin').write_bytes(raw)
        (directory / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
        stride = LIMITS['OUTPUT_WORDS'] * 4
        old_digest = hashlib.sha256()
        changed = []
        for index, block in zip(indices, manifest['blocks']):
            view = memoryview(raw)[index * stride:(index + 1) * stride]
            old_digest.update(view)
            actual = hashlib.sha256(view).hexdigest()
            if actual != block['sha256']:
                changed.append(dict(**block, current_index=index, actual_sha256=actual))
        projection = dict(passed=not changed and old_digest.hexdigest() == prior['output_sha256'],
                          prior_proof_commit=PRIOR, block_proof_commit=BLOCK_PROOF,
                          source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                          compute_worktree_clean=subprocess.run(['git', 'diff', '--quiet', '--', 'app', 'scripts', 'gpu', 'tests'], cwd=ROOT).returncode == 0,
                          prior_inputs=2182, current_inputs=len(programs), current_positive_inputs=len(cases),
                          input_projection='ABI6C to6B only; every other prior input byte preserved',
                          prior_input_sha256=prior['input_sha256'], prior_output_sha256=prior['output_sha256'],
                          projected_input_sha256=digest.hexdigest(), projected_output_sha256=old_digest.hexdigest(),
                          changed=changed, all_old_output_words_equal=not changed, no_gpu_retry=True,
                          gpu_execution_reused=bool(args.replay), replay_source=str(args.replay) if args.replay else None,
                          no_output_normalization=True, input_path=str(directory / 'input.bin'), raw_path=str(directory / 'readback.bin'),
                          driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), evidence=evidence)
        (ROOT / f'research/portable-probability-existing-{args.backend}-parity.json').write_text(json.dumps(projection, indent=2) + '\n')
        assert projection['passed'], f'Prior output changed; full current bytes retained at {directory}'
        return raw, evidence

    runtime.dispatch_programs = captured
    old_argv = sys.argv
    sys.argv = [sys.argv[0], '--backend', args.backend] + (['--batch-size', str(args.batch_size)] if args.batch_size is not None else [])
    try:
        verifier.main()
        assert calls == 1
    finally:
        runtime.dispatch_programs = original
        sys.argv = old_argv
    path = ROOT / f'research/portable-combat-{args.backend}.json'
    result = json.loads(path.read_text())
    assert result['passed'] and result['rejected_cases'][:len(prior['rejected_cases'])] == prior['rejected_cases']
    assert result['cases'][:len(prior['cases'])] == prior['cases']
    for key in prior:
        if key.endswith('_cpu_regressions') or key.startswith('known_'):
            assert result[key] == prior[key], key
    result['probability_existing_parity'] = projection
    path.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
    print('All2182 prior input bytes,output words,decoded cases and native groups preserved')


if __name__ == '__main__':
    main()
