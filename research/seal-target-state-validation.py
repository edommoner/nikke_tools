"""Seal full Metal plus new/saved source-identical CUDA evidence honestly."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE='795a9e5b684796b3b6a2fb9b59546e60401a5503'
PRIOR='3f6342fcee8d5d2773a89307597dbd5bd184f01e'
def load(name):return json.loads((P/(name+'.json')).read_text())
def save(name,value):(P/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    broad=load('portable-target-states-broad-validation');transfer=load('portable-target-states-transfer-completed')
    decision=load('portable-target-states-efficiency-decision');m=load('portable-combat-metal')
    w=load('windows-portable-target-states-v71');audit=load('portable-catalog-readiness');favorite=load('portable-favorite-readiness')
    assert all(x['passed'] and x['source_commit']==SOURCE for x in (broad,transfer,decision))
    assert broad['all_current_gates_passed'] and broad['mac_gates']==35
    assert transfer['artifact_transfer_complete'] and transfer['windows_execution_terminal']
    assert transfer['all_current_input_and_output_bytes_compared'] and transfer['verification_mode']=='incremental'
    assert transfer['current_source_actual_cuda_inputs']==251 and transfer['source_identical_saved_cuda_inputs']==2503
    assert decision['efficiency_evaluated'] and not decision['production_change_adopted']
    subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
    assert m['passed'] and w['passed'] and len(m['cases'])==2363 and len(m['rejected_cases'])==391
    assert len(m['target_state_cpu_regressions'])==233 and len(w['cases'])==233
    assert len([c for c in m['cases'] if c['name'].startswith('target-state-alias-')])==30
    assert favorite['passed'] and audit['own_effect_preflight_passed']==54 and sum(audit['issues'].values())==345
    cuda=dict(passed=True,backend='cuda',verification_mode='incremental',source_commit=SOURCE,
        logical_total_inputs=2754,current_source_actual_gpu_inputs=251,source_identical_saved_gpu_inputs=2503,
        current_component_report='windows-portable-target-states-v71.json',prior_report='windows-portable-target-states-v70.json',
        transfer_receipt='portable-target-states-transfer-completed.json',all_current_input_and_output_bytes_compared=True,
        source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],
        current_component_input_sha256=w['input_sha256'],current_component_output_sha256=w['output_sha256'],
        gpu_execution_verified=True,all_inputs_freshly_executed=False,execution=w['execution'],postcheck=w['postcheck'],
        scope='251 current inputs executed;2503 old input/source-identical saved CUDA outputs reused;both partitions match full current Metal bytes')
    save('portable-combat-cuda',cuda)
    proof=dict(passed=True,source_commit=SOURCE,previous_proof_commit=PRIOR,
        checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),wire_abi='0x5045566E',
        mac_gates=35,unit_tests=249,core_programs=2754,positive_cases=2363,rejections=391,
        target_state_native_cases=233,target_state_api_cases=10,target_stack_alias_cases=30,
        geometry_native_cases=190,probability_native_cases=92,real_profiles=108,old_profiles_preserved=104,
        previous_2503_output_words_preserved=True,current_full_metal_core_gpu_replayed=False,
        cuda_verification_mode='incremental',current_source_actual_cuda_inputs=251,source_identical_saved_cuda_inputs=2503,
        windows_gpu_executions_current_source=1,previous_v70_diagnostic_gpu_executions=1,additional_transfer_gpu_runs=0,
        windows_execution=w['execution'],windows_postcheck=w['postcheck'],transfer=transfer,
        efficiency_decision=decision,production_change_adopted=False,selected_candidate_requires_new_source_validation=decision['selected_for_adoption'],
        own_effect_preflight_passed=54,unadmitted_effects=345,
        favorite_preflight_contexts=favorite['own_effect_preflight_contexts_passed'],favorite_all_four_stage_candidates=favorite['all_four_stages_preflight_characters'],
        initial_expiry_finding='portable-target-states-first-finding.json',alias_metadata_finding='portable-target-stack-alias-finding.json',
        initial_aborted_gate_run='portable-target-states-initial-gates-aborted.json',
        initial_unlocalized_metal_finding_open=True,full_character_verified=0,full_goal_complete=False,normal_ui_backend='cpu',
        input_sha256=m['input_sha256'],output_sha256=m['output_sha256'])
    save('portable-target-states-validation',proof)
    checkpoint=dict(wire_abi='0x5045566E',verified_commit=SOURCE,
        previous_checkpoint=dict(proof_commit=PRIOR,report='Git previous portable-combat-checkpoint.json'),
        positive_cases=2363,rejections=391,batched_inputs=2754,input_words=86016,output_words=159744,
        metal_verified=True,cuda_verified=True,metal_report='portable-combat-metal.json',cuda_report='portable-combat-cuda.json',
        windows_report='windows-portable-target-states-v71.json',cuda_verification_mode='incremental',
        current_source_actual_cuda_inputs=251,source_identical_saved_cuda_inputs=2503,
        source_provenance=dict(current_fixed_source_commit=SOURCE,retained_cuda_source_commit='36bde18ca18e64f910e9bc5baf586e6a7ba9dfee',
                               retained_gpu_source_bytes_identical=True,previous_full_proof_commit=PRIOR),
        validation_receipt='portable-target-states-validation.json',generated_source_comparison=transfer['normalized_generated_sha256'],
        existing_parity=m['target_state_existing_parity'],mac_gates=35,unit_tests=249,real_roster_profiles=108,real_fixed_squad=8,
        weapon_only_metal_verified=203,real_equipment_initialization_squads=203,normal_ui_connected=False,normal_ui_backend='cpu',
        catalog_characters=203,own_effect_preflight_passed=54,full_character_verified=0,all_characters_supported=False,full_goal_complete=False,
        cpu_trace_used_as_gpu_input=False,missing_families=audit['missing_families'],
        regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},source_sha256=m['source_sha256'],validation_sha256=m['validation_sha256'],
        input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],batch_layout=m['batch_layout'],
        current_full_metal_core_executed=True,current_full_cuda_core_freshly_executed=False,
        all_current_cuda_input_output_bytes_compared=True,initial_metal_finding_open=True,
        initial_metal_finding='portable-element-initial-core-finding.json',
        target_state=dict(native_cases=233,alias_cases=30,new_runtime_arrays=0,stack_policy='max instance',
            presence_policy='any live enemy',runtime_recheck='presence only;stack threshold activation-only',compiler_metadata_preserved=True),
        efficiency_decision='portable-target-states-efficiency-decision.json',
        next_work='Validate selected optimization before adoption if any;then remaining effects/world/all203 variants')
    save('portable-combat-checkpoint',checkpoint)
    names=['portable-target-states-validation','portable-combat-checkpoint','portable-combat-cuda','portable-combat-metal',
        'portable-target-states-broad-validation','portable-target-states-global-gates','portable-target-states-transfer-completed',
        'portable-target-states-timing-order','portable-target-states-benchmark','portable-target-states-candidate-parity',
        'portable-target-states-efficiency-decision','portable-target-states-existing-metal-parity',
        'portable-target-states-incremental-cuda-parity','windows-portable-target-states-v71',
        'portable-target-states-v70-reuse-manifest','windows-portable-target-states-v70',
        'portable-target-states-transfer-completed-v70','portable-target-states-existing-cuda-parity',
        'portable-target-states-existing-metal-parity-v70','portable-target-states-initial-core-metal',
        'portable-target-states-initial-gates-aborted','portable-target-states-first-finding',
        'portable-target-states-first-metal','portable-target-states-initial-expiry-fixed-metal','portable-target-stack-alias-finding',
        'portable-target-states-native','portable-favorite-readiness','portable-attack-flags-native']
    paths=[P/(n+'.json') for n in names]
    paths += [P/n for n in ['seal-target-state-gates.py','seal-target-state-incremental-cuda.py','seal-target-state-validation.py',
        'benchmark-target-states.py','decide-target-state-efficiency.py','verify-target-state-incremental-cuda.py','characterize-attack-flags.py','verify-target-stack-alias-gap.py']]
    paths += [ROOT/'docs'/n for n in ['mac-handoff.md','mac-migration.md','portable-combat-runtime.md']]
    save('portable-target-states-receipt',dict(passed=True,source_commit=SOURCE,
        artifact_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}))
    print('Full Metal and incremental CUDA evidence sealed;full203 goal remains incomplete')

if __name__=='__main__':main()
