"""Freeze authored inputs and separate full native counter observations, GPU0."""
import array
import hashlib
import json
import subprocess
import struct
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'scripts', 'research')]
import portable_target_counter_specs as wire
from target_counter_cases import clone_cases
from world_target_counter_native import NAMES, observe_case, activation_child_witness
import detail_gpu
import engine_worker


def main():
    rows = clone_cases(); inputs = []; observations = []; compiler_checks = 0
    chars = [dict(name=n, skill_levels={'1':10, '2':10, '3':10}, _weapon=engine_worker.META[n]) for n in NAMES]
    with patch('portable_backend.execute', side_effect=AssertionError('GPU forbidden')), patch('portable_backend.execute_batches', side_effect=AssertionError('GPU forbidden')), patch('detail_gpu.run', side_effect=AssertionError('GPU forbidden')):
        for case in rows:
            compiled = detail_gpu.compile_effects(chars, [(e, NAMES[0]) for e in case['effects']])
            names = compiled['states']
            words = wire.pack([(e, 0) for e in case['effects']], case['actions'], NAMES, names)
            for i, row in enumerate(compiled['effects']):
                at = wire.POLICY_BASE + i * wire.POLICY_WORDS; p = words[at:at + wire.POLICY_WORDS]
                threshold = struct.unpack('<d', struct.pack('<II', *p[4:6]))[0]
                assert [threshold, *p[1:4], p[6], p[7], p[8]&1, (p[8]>>1)&1, (p[8]>>2)&1] == row[295:304]
                assert p[9:11] == [int(row[0]), int(row[3])]
                compiler_checks += 1
            data = array.array('I', words)
            if sys.byteorder != 'little': data.byteswap()
            raw = data.tobytes()
            inputs.append(dict(name=case['name'], words=len(words), sha256=hashlib.sha256(raw).hexdigest()))
            observations.append(observe_case(case))
        witness = activation_child_witness()
    report = dict(passed=True, scope='Literal input encoding and actual native resource/event oracle; GPU executor not connected',
        source_parent=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        schema=dict(magic=wire.MAGIC, version=wire.VERSION, input_words=wire.INPUT_WORDS,
                    policy_base=wire.POLICY_BASE, policy_words=wire.POLICY_WORDS,
                    action_base=wire.ACTION_BASE, action_words=wire.ACTION_WORDS),
        inputs=inputs, cases=observations, activation_child_witness=witness, common_compiler_policy_rows_checked=compiler_checks,
        cpu_state_used_as_gpu_input=False, gpu_executions=0, normal_ui='CPU', canonical_world_admission=False,
        full_character_verified=0, full_goal_complete=False)
    destination = ROOT / 'research/portable-world-target-counter-native-contract.json'
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print('Native counter contracts', len(rows), 'steps', sum(len(r['steps']) for r in observations), 'activation-child witness1; GPU0')


if __name__ == '__main__': main()
