"""Verify recovered current CUDA results before allowing an efficiency experiment.

The earlier proof at e4ea13c remains historical. This receipt does not declare
the full catalog or the optimization stage complete.
"""
import argparse, datetime, hashlib, importlib.util, json, os, subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
P = R / 'research'
SOURCE = 'dd7d62b98a63f9fa99892dd964809775b136a9d6'
def load(name): return json.loads((P / (name + '.json')).read_text())
def save(name, value): (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main(args):
    w = load('windows-portable-combat-v63')
    m = load('portable-combat-metal')
    g = load('portable-enemy-codes-global-gates')
    assert w['passed'] and w['gpu_execution_verified'] and w['current_full_cuda_batch_executed']
    e, post = w['execution'], w['postcheck']
    assert e['commit'] == SOURCE and e['exit_code'] == 0 and not e['timed_out']
    assert e['below_normal_priority'] and e['timeout_seconds'] == 120
    assert post['remaining_verification_processes'] == 0 and post['existing_gpu_service_preserved']
    for field in ('head', 'status'): assert e['original_' + field + '_before'] == post['original_' + field + '_after']
    assert sha(P / 'windows-portable-combat-v63.json') == args.raw_sha256
    assert args.parts > 0
    assert len(m['cases']) == 1692 and len(m['rejected_cases']) == 314
    assert len(m['enemy_code_cpu_regressions']) == 103
    assert m['passed'] and g['passed'] and g['complete'] and len(g['gates']) == 29
    assert g['source_commit'] == SOURCE and all(x['source_commit'] == SOURCE and x['exit_code'] == 0 for x in g['gates'])
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=R, check=True, stdout=subprocess.DEVNULL)
    keys = ['source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256', 'actual_statuses', 'expected_statuses', 'batch_layout', 'rejected_cases']
    keys += [k for k in m if k.endswith('_cpu_regressions') or k.startswith('known_')]
    for key in keys: assert w[key] == m[key], key
    assert w['cases'] == [dict(name=c['name'], passed=c['passed']) for c in m['cases']]
    for group in ('source_sha256', 'validation_sha256'):
        for path, digest in m[group].items():
            assert sha(R / path) == digest, path
            assert hashlib.sha256(subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=R)).hexdigest() == digest, path
    spec = importlib.util.spec_from_file_location('normalizer', P / 'seal-stack-increment.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    normalized = {}
    for backend, suffix in (('cuda', 'cu'), ('metal', 'metal')):
        path = P / 'portable-build' / ('event_runtime.' + suffix)
        assert sha(path) == m['generated_sha256'][backend]
        normalized[backend] = helper.normalized(path.read_bytes())
        assert normalized[backend] == w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256'], backend
    a, b = load('portable-enemy-codes-existing-metal-parity'), w['enemy_code_existing_parity']
    assert a['passed'] and b['passed'] and a['prior_inputs'] == b['prior_inputs'] == 1893
    for key in ('source_sha256', 'input_sha256', 'output_sha256', 'prior_input_sha256', 'prior_output_sha256', 'prior_inputs', 'current_inputs', 'all_old_output_words_equal', 'no_output_normalization'):
        assert a[key] == b[key], key
    transfer = dict(passed=True, windows_report='windows-portable-combat-v63.json', parts=args.parts, total_parts=args.parts, remote_turn_status='completed', remote_turn=args.remote_turn, decoded_sha256=args.raw_sha256, windows_execution_terminal=True, remaining_verification_processes=0, current_full_cuda_batch_executed=True, compared_keys=keys)
    transfer['remote_execution_turn']=args.remote_turn
    transfer['transfer_turns']=[dict(turn_id=t,status='completed') for t in (args.transfer_turns or [args.remote_turn])]
    save('portable-enemy-codes-transfer-completed', transfer)
    save('portable-enemy-codes-existing-cuda-parity', b)
    save('portable-enemy-codes-generated-comparison', dict(passed=True, source_commit=SOURCE, normalized_sha256=normalized, compared_keys=keys))
    save('portable-enemy-codes-pre-optimization', dict(passed=True, source_commit=SOURCE, source_sha256=m['source_sha256'], validation_sha256=m['validation_sha256'], input_sha256=m['input_sha256'], output_sha256=m['output_sha256'], mac_gates=29, positive_cases=1692, rejections=314, batched_inputs=2006, unit_tests=212, windows_report='windows-portable-combat-v63.json', current_full_cuda_batch_executed=True, full_goal_complete=False, efficiency_evaluated=False))
    if args.timing_order:
        processes = []
        for line in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,etime=,command='], text=True).splitlines():
            fields = line.split(None, 3)
            if len(fields) != 4: continue
            pid, ppid, elapsed, command = fields
            if int(pid) == os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh', '/bin/bash')): continue
            if any(token in command for token in (' research/run-', ' research/verify-', ' scripts/verify-portable-', '/scripts/run-metal-probe.swift', ' research/benchmark-')):
                processes.append(dict(pid=int(pid), ppid=int(ppid), elapsed=elapsed, command=command))
        assert not processes, processes
        assert not (P / 'portable-enemy-codes-timing-order.json').exists()
        save('portable-enemy-codes-timing-order', dict(passed=True, checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_commit=SOURCE, all_mac_gates_complete=True, mac_gates=29, windows_execution_and_transfer_terminal=True, verification_processes=processes, transfer=transfer))
    print('Current2006-input CUDA and Metal results,29 Mac gates and transfer verified; full catalog remains incomplete')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--raw-sha256', required=True)
    p.add_argument('--parts', type=int, required=True)
    p.add_argument('--remote-turn', required=True)
    p.add_argument('--timing-order', action='store_true')
    p.add_argument('--transfer-turns', nargs='+')
    main(p.parse_args())
