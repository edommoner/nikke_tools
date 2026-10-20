"""Seal the unchanged production source after evaluating a non-adopted candidate."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
P = R / 'research'
SOURCE = 'dd7d62b98a63f9fa99892dd964809775b136a9d6'
def load(name): return json.loads((P / (name + '.json')).read_text())
def save(name, value): (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    m, w = load('portable-combat-metal'), load('windows-portable-combat-v63')
    pre, decision = load('portable-enemy-codes-pre-optimization'), load('portable-enemy-codes-efficiency-decision')
    transfer, gates = load('portable-enemy-codes-transfer-completed'), load('portable-enemy-codes-global-gates')
    assert pre['passed'] and decision['passed'] and decision['efficiency_evaluated'] and not decision['production_change_adopted']
    assert transfer['passed'] and transfer['remote_turn_status'] == 'completed' and transfer['parts'] == transfer['total_parts'] == 9
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 29 and gates['source_commit'] == SOURCE
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=R, check=True, stdout=subprocess.DEVNULL)
    for key in ('source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256'):
        assert m[key] == pre[key] == w[key], key
    assert m['passed'] and w['passed'] and w['execution']['commit'] == SOURCE
    assert sha(P / 'windows-portable-combat-v63.json') == transfer['decoded_sha256']
    for group in ('source_sha256', 'validation_sha256'):
        for path, digest in m[group].items(): assert sha(R / path) == digest, path
    for name in ('portable-enemy-codes-generated-comparison', 'portable-enemy-codes-existing-metal-parity', 'portable-enemy-codes-existing-cuda-parity', 'portable-enemy-codes-roster-parity'):
        assert load(name)['passed'], name
    assert load('portable-roster-battles-metal')['passed'] and len(load('portable-roster-battles-metal')['cases']) == 86
    assert load('portable-api-metal')['passed'] and len(load('portable-api-metal')['enemy_code_execution']) == 5
    processes = []
    for line in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,etime=,command='], text=True).splitlines():
        fields = line.split(None, 3)
        if len(fields) != 4: continue
        pid, ppid, elapsed, command = fields
        if int(pid) == os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh', '/bin/bash')): continue
        if any(token in command for token in (' research/run-', ' research/verify-', ' scripts/verify-portable-', '/scripts/run-metal-probe.swift', ' research/benchmark-')):
            processes.append(dict(pid=int(pid), ppid=int(ppid), elapsed=elapsed, command=command))
    assert not processes, processes
    save('portable-enemy-codes-final-processes', dict(passed=True, checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), verification_processes=processes, windows_transfer=transfer))
    save('portable-combat-cuda', dict(w, summary_only=True, summary_source='windows-portable-combat-v63.json', scope=m['scope']))
    (P / 'portable-combat-v62-checkpoint.json').write_bytes(subprocess.check_output(['git', 'show', '0066afe:research/portable-combat-checkpoint.json'], cwd=R))
    audit = load('portable-catalog-readiness')
    checkpoint = dict(wire_abi='0x5045566A', verified_commit=SOURCE, previous_checkpoint=dict(report='portable-combat-v62-checkpoint.json', proof_commit='0066afe'), positive_cases=1692, rejections=314, batched_inputs=2006, input_words=86016, output_words=159744, metal_verified=True, cuda_verified=True, metal_report='portable-combat-metal.json', cuda_report='portable-combat-cuda.json', windows_report='windows-portable-combat-v63.json', windows_execution=w['execution'], windows_postcheck=w['postcheck'], windows_checks_this_stage=1, current_full_cuda_batch_executed=True, cuda_verification_mode='full_current_batch', source_provenance=dict(fixed_shared_source_commit=SOURCE, metal_core_source_commit=SOURCE, windows_source_commit=SOURCE), validation_receipt='portable-enemy-codes-validation.json', generated_source_comparison='portable-enemy-codes-generated-comparison.json', existing_parity='portable-enemy-codes-existing-metal-parity.json', mac_gates=29, unit_tests=212, real_roster_profiles=86, real_fixed_squad=8, weapon_only_metal_verified=203, real_equipment_initialization_squads=203, normal_ui_connected=False, normal_ui_backend='cpu', catalog_characters=203, own_effect_preflight_passed=audit['own_effect_preflight_passed'], full_character_verified=0, all_characters_supported=False, full_goal_complete=False, cpu_trace_used_as_gpu_input=False, regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')}, missing_families=audit['missing_families'], ordered_delivery=dict(max_recipients=21, order_and_duplicates_preserved=True, instant_lists_connected=True, instant_native_cases=45, instant_api_cases=8, split_native_cases=46, protection_native_cases=57, previous_efficiency='0066afe:research/portable-named-states-efficiency-decision.json'), historical_measurement_scope='Earlier metrics retain their original source and proof provenance in the previous checkpoint; the current experiment is separate.', next_work=['Connect remaining modifiers, controls, enemy world scheduling and effects; certify all203 characters and their variants'])
    checkpoint['enemy_codes']=dict(native_cases=103,api_cases=5,code_specific_real_profiles=6,predicate_id=44,legacy_folded_id_rejected=22,exact_ids=True,global_code_not_target_dependent=True,missing_code_passes=True,active_mode_projection=True,private_fields_added=0,efficiency=decision)
    for key in ('source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256', 'batch_layout'): checkpoint[key] = m[key]
    save('portable-combat-checkpoint', checkpoint)
    reports = ['portable-combat-checkpoint', 'portable-combat-v62-checkpoint', 'portable-combat-metal', 'portable-combat-cuda', 'windows-portable-combat-v63', 'portable-enemy-codes-transfer-completed', 'portable-enemy-codes-generated-comparison', 'portable-enemy-codes-existing-metal-parity', 'portable-enemy-codes-existing-cuda-parity', 'portable-enemy-codes-global-gates', 'portable-enemy-codes-pre-optimization', 'portable-enemy-codes-timing-order', 'portable-enemy-codes-efficiency-decision', 'portable-enemy-codes-roster-parity', 'portable-enemy-codes-unit-tests', 'portable-enemy-codes-candidate-parity', 'portable-enemy-codes-benchmark', 'portable-enemy-codes-final-processes', 'portable-enemy-codes-broad-validation', 'portable-enemy-codes-metal', 'portable-enemy-codes-native', 'portable-enemy-code-real-metal', 'portable-enemy-codes-oracle-budgets-failure', 'portable-code-context-stimulus-correction', 'portable-code-real-projection-gap', 'portable-enemy-code-storage', 'portable-roster-battles-metal', 'portable-api-metal', 'portable-catalog-readiness', 'portable-catalog-weapons-metal', 'portable-real-equipment-metal', 'portable-real-battle-metal', 'portable-events-metal', 'portable-numeric-metal', 'portable-probe-metal', 'portable-metal-pipeline-lock', 'portable-duration-extend-metal', 'portable-definition-input-metal', 'portable-definition-scalar-metal', 'portable-definition-out-metal', 'portable-removal-queue-metal', 'portable-stack-numeric-metal', 'portable-stack-notices-metal']
    tools = ['seal-code-cuda.py', 'finalize-code-proof.py', 'benchmark-codes.py', 'verify-code-regression.py', 'run-code-gates.py', 'seal-code-gates.py', 'build-code-cases.py', 'verify-codes.py', 'verify-code-real.py', 'verify-code-storage.py']
    docs = ['portable-enemy-codes.md', 'mac-handoff.md', 'mac-migration.md', 'portable-combat-runtime.md']
    save('portable-enemy-codes-validation', dict(passed=True, checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_commit=SOURCE, positive_cases=1692, rejections=314, batched_inputs=2006, unit_tests=212, mac_gates=29, real_profiles=86, current_full_cuda_batch_executed=True, normal_ui_backend='cpu', full_character_verified=0, full_goal_complete=False, efficiency_evaluated=True, efficiency_adopted=False, previous_proof=dict(proof_commit='0066afe', path='research/portable-named-states-validation.json'), artifact_scope=dict(current_gpu='Current2006-input core,103 component cases,86 real profiles and29 Mac gates plus6 code-specific profiles',diagnostics='Initial observer budgets,context stimulus and active-mode projection findings retain their earlier provenance',future_work='Separate damage-effect target_code field remains unported'),scope='Current common CUDA/Metal mechanics and29 Mac gates; earlier receipts retain their commit-specific provenance; full catalog remains incomplete.', artifact_sha256={'research/'+n+'.json':sha(P/(n+'.json')) for n in reports}, tool_sha256={'research/'+n:sha(P/n) for n in tools}, documentation_sha256={'docs/'+n:sha(R/'docs'/n) for n in docs}))
    print('Current CUDA/Metal proofs sealed; candidate not adopted; full catalog remains incomplete')

if __name__ == '__main__': main()
