"""Seal the unchanged production source after evaluating a non-adopted candidate."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
P = R / 'research'
SOURCE = 'ed68e6847fe8e7f0d13ed81a6af6dec6837ca915'
def load(name): return json.loads((P / (name + '.json')).read_text())
def save(name, value): (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    m, w = load('portable-combat-metal'), load('windows-portable-combat-v62')
    pre, decision = load('portable-named-states-pre-optimization'), load('portable-named-states-efficiency-decision')
    transfer, gates = load('portable-named-states-transfer-completed'), load('portable-named-states-global-gates')
    assert pre['passed'] and decision['passed'] and decision['efficiency_evaluated'] and not decision['production_change_adopted']
    assert transfer['passed'] and transfer['remote_turn_status'] == 'completed' and transfer['parts'] == transfer['total_parts'] == 9
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 27 and gates['source_commit'] == SOURCE
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=R, check=True, stdout=subprocess.DEVNULL)
    for key in ('source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256'):
        assert m[key] == pre[key] == w[key], key
    assert m['passed'] and w['passed'] and w['execution']['commit'] == SOURCE
    assert sha(P / 'windows-portable-combat-v62.json') == transfer['decoded_sha256']
    for group in ('source_sha256', 'validation_sha256'):
        for path, digest in m[group].items(): assert sha(R / path) == digest, path
    for name in ('portable-named-states-generated-comparison', 'portable-named-states-existing-metal-parity', 'portable-named-states-existing-cuda-parity', 'portable-named-states-roster-parity'):
        assert load(name)['passed'], name
    assert load('portable-roster-battles-metal')['passed'] and len(load('portable-roster-battles-metal')['cases']) == 84
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
    save('portable-named-states-final-processes', dict(passed=True, checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), verification_processes=processes, windows_transfer=transfer))
    save('portable-combat-cuda', dict(w, summary_only=True, summary_source='windows-portable-combat-v62.json', scope=m['scope']))
    (P / 'portable-combat-v60-checkpoint.json').write_bytes(subprocess.check_output(['git', 'show', 'e4ea13c:research/portable-combat-checkpoint.json'], cwd=R))
    audit = load('portable-catalog-readiness')
    checkpoint = dict(wire_abi='0x50455669', verified_commit=SOURCE, previous_checkpoint=dict(report='portable-combat-v60-checkpoint.json', proof_commit='e4ea13c'), positive_cases=1589, rejections=304, batched_inputs=1893, input_words=86016, output_words=159744, metal_verified=True, cuda_verified=True, metal_report='portable-combat-metal.json', cuda_report='portable-combat-cuda.json', windows_report='windows-portable-combat-v62.json', windows_execution=w['execution'], windows_postcheck=w['postcheck'], windows_checks_this_stage=2, current_full_cuda_batch_executed=True, cuda_verification_mode='full_current_batch', source_provenance=dict(fixed_shared_source_commit=SOURCE, metal_core_source_commit=SOURCE, windows_source_commit=SOURCE), validation_receipt='portable-named-states-validation.json', generated_source_comparison='portable-named-states-generated-comparison.json', existing_parity='portable-named-states-existing-metal-parity.json', mac_gates=27, unit_tests=195, real_roster_profiles=84, real_fixed_squad=8, weapon_only_metal_verified=203, real_equipment_initialization_squads=203, normal_ui_connected=False, normal_ui_backend='cpu', catalog_characters=203, own_effect_preflight_passed=audit['own_effect_preflight_passed'], full_character_verified=0, all_characters_supported=False, full_goal_complete=False, cpu_trace_used_as_gpu_input=False, regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')}, missing_families=audit['missing_families'], ordered_delivery=dict(max_recipients=21, order_and_duplicates_preserved=True, instant_lists_connected=True, instant_native_cases=45, instant_api_cases=8, split_native_cases=46, protection_native_cases=57, previous_efficiency='e4ea13c:research/portable-instant-lists-efficiency-decision.json'), historical_measurement_scope='Earlier metrics retain their original source and proof provenance in the previous checkpoint; the current experiment is separate.', next_work=['Connect remaining modifiers, controls, enemy world scheduling and effects; certify all203 characters and their variants'])
    checkpoint['base_weapon_classification']=dict(field='base_weapon_type',wire='attackContext bit2',explosion_requires_current_charge_path=True,immutable_base_type_survives_modes=True,real_mint_profiles=2,all_prepared_effects_included=True,private_fields_added=0)
    checkpoint['named_states']=dict(native_cases=65,typed_stat_applied_notices=['dot_dmg_pct','split_dmg_pct'],exact_colon_names=True,captured_recipient_order=True,lazy_targets_do_not_emit=True,efficiency=decision)
    for key in ('source_sha256', 'validation_sha256', 'input_sha256', 'output_sha256', 'batch_layout'): checkpoint[key] = m[key]
    save('portable-combat-checkpoint', checkpoint)
    reports = ['portable-combat-checkpoint', 'portable-combat-v60-checkpoint', 'portable-combat-metal', 'portable-combat-cuda', 'windows-portable-combat-v62', 'portable-named-states-transfer-completed', 'portable-named-states-generated-comparison', 'portable-named-states-existing-metal-parity', 'portable-named-states-existing-cuda-parity', 'portable-named-states-global-gates', 'portable-named-states-pre-optimization', 'portable-named-states-timing-order', 'portable-named-states-efficiency-decision', 'portable-named-states-roster-parity', 'portable-named-states-unit-tests', 'portable-roster-battles-metal', 'portable-api-metal', 'portable-catalog-readiness']
    for name in ('portable-named-states-candidate-parity', 'portable-named-states-benchmark', 'portable-named-states-initial-failure'):
        if (P / (name + '.json')).exists(): reports.append(name)
    reports += ['windows-portable-combat-v61','portable-named-states-initial-global-gates','portable-named-states-initial-gaps','portable-named-state-alias-probe','portable-mint-real-metal','portable-named-state-storage','portable-named-state-fixture-field-correction','portable-next-code-native','portable-next-code-predicate-design','portable-named-states-final-processes','portable-named-states-broad-validation','portable-named-states-metal','portable-named-states-native','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-stack-numeric-metal','portable-stack-notices-metal']
    tools = ['seal-named-state-cuda.py', 'finalize-named-state-proof.py', 'benchmark-named-states.py', 'verify-named-state-regression.py', 'run-named-state-gates.py','seal-named-state-gates.py','build-named-state-cases.py','verify-named-states.py','verify-mint-real.py','verify-next-code-native.py','verify-named-state-storage.py']
    docs = ['portable-named-states.md', 'mac-handoff.md', 'mac-migration.md', 'portable-combat-runtime.md']
    save('portable-named-states-validation', dict(passed=True, checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_commit=SOURCE, positive_cases=1589, rejections=304, batched_inputs=1893, unit_tests=195, mac_gates=27, real_profiles=84, current_full_cuda_batch_executed=True, normal_ui_backend='cpu', full_character_verified=0, full_goal_complete=False, efficiency_evaluated=True, efficiency_adopted=False, previous_proof=dict(proof_commit='e4ea13c', path='research/portable-instant-lists-validation.json'), artifact_scope=dict(current_gpu='Current1893-input core,65 component cases,84 real profiles and27 Mac gates',diagnostics='Initial stat notice,alias and Mint failures retain their earlier source provenance',future_work='Enemy code design/native probes do not admit or certify that GPU feature'),scope='Current common CUDA/Metal mechanics and27 Mac gates; earlier receipts retain their commit-specific provenance; full catalog remains incomplete.', artifact_sha256={'research/'+n+'.json':sha(P/(n+'.json')) for n in reports}, tool_sha256={'research/'+n:sha(P/n) for n in tools}, documentation_sha256={'docs/'+n:sha(R/'docs'/n) for n in docs}))
    print('Current CUDA/Metal proofs sealed; candidate not adopted; full catalog remains incomplete')

if __name__ == '__main__': main()
