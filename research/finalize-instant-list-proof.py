"""Seal the unchanged production source after evaluating a non-adopted candidate."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
P = R / 'research'
SOURCE = '60a10b694516c8f2fb7594911585326aebc14a56'
def load(name): return json.loads((P / (name + '.json')).read_text())
def save(name, value): (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    m, w = load('portable-combat-metal'), load('windows-portable-combat-v60')
    pre, decision = load('portable-instant-lists-pre-optimization'), load('portable-instant-lists-efficiency-decision')
    transfer, gates = load('portable-instant-lists-transfer-completed'), load('portable-instant-lists-global-gates')
    assert pre['passed'] and decision['passed'] and decision['efficiency_evaluated'] and not decision['production_change_adopted']
    assert transfer['passed'] and transfer['remote_turn_status'] == 'completed' and transfer['parts'] == transfer['total_parts'] == 8
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 26 and gates['source_commit'] == SOURCE
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=R, check=True, stdout=subprocess.DEVNULL)
    for key in ('source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256'):
        assert m[key] == pre[key] == w[key], key
    assert m['passed'] and w['passed'] and w['execution']['commit'] == SOURCE
    assert sha(P / 'windows-portable-combat-v60.json') == transfer['decoded_sha256']
    for group in ('source_sha256', 'validation_sha256'):
        for path, digest in m[group].items(): assert sha(R / path) == digest, path
    for name in ('portable-instant-lists-generated-comparison', 'portable-instant-lists-existing-metal-parity', 'portable-instant-lists-existing-cuda-parity', 'portable-instant-lists-roster-parity'):
        assert load(name)['passed'], name
    assert load('portable-instant-list-normal-fixed-metal')['full_instant_list_supported']
    assert load('portable-roster-battles-metal')['passed'] and len(load('portable-roster-battles-metal')['cases']) == 82
    assert load('portable-api-metal')['passed'] and len(load('portable-api-metal')['instant_list_execution']) == 8
    processes = []
    for line in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,etime=,command='], text=True).splitlines():
        fields = line.split(None, 3)
        if len(fields) != 4: continue
        pid, ppid, elapsed, command = fields
        if int(pid) == os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh', '/bin/bash')): continue
        if any(token in command for token in (' research/run-', ' research/verify-', ' scripts/verify-portable-', '/scripts/run-metal-probe.swift', ' research/benchmark-')):
            processes.append(dict(pid=int(pid), ppid=int(ppid), elapsed=elapsed, command=command))
    assert not processes, processes
    save('portable-instant-lists-final-processes', dict(passed=True, checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), verification_processes=processes, windows_transfer=transfer))
    save('portable-combat-cuda', dict(w, summary_only=True, summary_source='windows-portable-combat-v60.json', scope=m['scope']))
    (P / 'portable-combat-v58-checkpoint.json').write_bytes(subprocess.check_output(['git', 'show', 'b8ae1c7:research/portable-combat-checkpoint.json'], cwd=R))
    audit = load('portable-catalog-readiness')
    checkpoint = dict(wire_abi='0x50455667', verified_commit=SOURCE, previous_checkpoint=dict(report='portable-combat-v58-checkpoint.json', proof_commit='b8ae1c7'), positive_cases=1524, rejections=300, batched_inputs=1824, input_words=86016, output_words=159744, metal_verified=True, cuda_verified=True, metal_report='portable-combat-metal.json', cuda_report='portable-combat-cuda.json', windows_report='windows-portable-combat-v60.json', windows_execution=w['execution'], windows_postcheck=w['postcheck'], windows_checks_this_stage=1, current_full_cuda_batch_executed=True, cuda_verification_mode='full_current_batch', source_provenance=dict(fixed_shared_source_commit=SOURCE, metal_core_source_commit=SOURCE, windows_source_commit=SOURCE), validation_receipt='portable-instant-lists-validation.json', generated_source_comparison='portable-instant-lists-generated-comparison.json', existing_parity='portable-instant-lists-existing-metal-parity.json', mac_gates=26, unit_tests=177, real_roster_profiles=82, real_fixed_squad=8, weapon_only_metal_verified=203, real_equipment_initialization_squads=203, normal_ui_connected=False, normal_ui_backend='cpu', catalog_characters=203, own_effect_preflight_passed=audit['own_effect_preflight_passed'], full_character_verified=0, all_characters_supported=False, full_goal_complete=False, cpu_trace_used_as_gpu_input=False, regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')}, missing_families=audit['missing_families'], ordered_delivery=dict(max_recipients=21, order_and_duplicates_preserved=True, instant_lists_connected=True, instant_native_cases=45, instant_api_cases=8, split_native_cases=46, protection_native_cases=57, efficiency=decision), historical_measurement_scope='Earlier metrics retain their original source and proof provenance in the previous checkpoint; the current experiment is separate.', next_work=['Connect remaining modifiers, controls, enemy world scheduling and effects; certify all203 characters and their variants'])
    for key in ('source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256', 'batch_layout'): checkpoint[key] = m[key]
    save('portable-combat-checkpoint', checkpoint)
    reports = ['portable-combat-checkpoint', 'portable-combat-v58-checkpoint', 'portable-combat-metal', 'portable-combat-cuda', 'windows-portable-combat-v59', 'windows-portable-combat-v60', 'portable-split-transfer-completed', 'portable-instant-lists-transfer-completed', 'portable-instant-lists-generated-comparison', 'portable-instant-lists-existing-metal-parity', 'portable-instant-lists-existing-cuda-parity', 'portable-instant-lists-global-gates', 'portable-instant-lists-pre-optimization', 'portable-instant-lists-timing-order', 'portable-instant-lists-efficiency-decision', 'portable-instant-lists-roster-parity', 'portable-instant-lists-unit-tests', 'portable-instant-list-normal-fixed-metal', 'portable-roster-battles-metal', 'portable-api-metal', 'portable-catalog-readiness']
    for name in ('portable-instant-lists-candidate-parity', 'portable-instant-lists-benchmark', 'portable-instant-lists-candidate-failure'):
        if (P / (name + '.json')).exists(): reports.append(name)
    reports.append('portable-instant-lists-final-processes')
    tools = ['seal-instant-list-cuda.py', 'finalize-instant-list-proof.py', 'benchmark-instant-lists.py', 'verify-instant-list-regression.py', 'run-instant-list-gates.py']
    docs = ['portable-instant-lists.md', 'mac-handoff.md', 'mac-migration.md', 'portable-combat-runtime.md']
    save('portable-instant-lists-validation', dict(passed=True, checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_commit=SOURCE, positive_cases=1524, rejections=300, batched_inputs=1824, unit_tests=177, mac_gates=26, real_profiles=82, current_full_cuda_batch_executed=True, normal_ui_backend='cpu', full_character_verified=0, full_goal_complete=False, efficiency_evaluated=True, efficiency_adopted=False, historical_mac_receipt=dict(proof_commit='c72b529', path='research/portable-instant-lists-metal-validation.json'), scope='Current common CUDA/Metal mechanics and26 Mac gates; historical Mac-only receipts retain their commit-specific provenance; full catalog remains incomplete.', artifact_sha256={'research/'+n+'.json':sha(P/(n+'.json')) for n in reports}, tool_sha256={'research/'+n:sha(P/n) for n in tools}, documentation_sha256={'docs/'+n:sha(R/'docs'/n) for n in docs}))
    print('Current CUDA/Metal proofs sealed; candidate not adopted; full catalog remains incomplete')

if __name__ == '__main__': main()
