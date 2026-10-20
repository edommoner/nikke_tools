"""Seal fixed-source physical attack flag proof; keep whole catalog goal open."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE='7492d8b191471f820989dc760bc4adc91494cf6a'
PRIOR='13c9bdf734fde4325db7376165fcc904b549a242'


def load(name):return json.loads((P/(name+'.json')).read_text())
def save(name,value,compact=False):
    options=dict(separators=(',',':')) if compact else dict(indent=2)
    (P/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,**options)+'\n')


def main():
    broad=load('portable-attack-flags-broad-validation');transfer=load('portable-attack-flags-transfer-completed')
    decision=load('portable-attack-flags-efficiency-decision')
    m=load('portable-combat-metal');w=load('windows-portable-attack-flags-v72')
    execution=load('portable-attack-flags-windows-execution')
    for r in (broad,transfer,decision):assert r['passed'] and r['source_commit']==SOURCE
    assert execution['passed'] and execution['source_commit']=='5a3ee26039dc031f98ccd34a9c3245ff606a8808'
    assert broad['all_current_gates_passed'] and broad['mac_gates']==37
    assert transfer['artifact_transfer_complete'] and transfer['windows_execution_terminal']
    assert decision['efficiency_evaluated'] and not decision['production_change_adopted']
    assert m['passed'] and w['passed'] and len(m['cases'])==2525 and len(m['rejected_cases'])==425
    assert len(m['attack_flag_cpu_regressions'])==162 and len(m['target_state_cpu_regressions'])==233
    subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
    for k in ('input_sha256','output_sha256','source_sha256','validation_sha256'):assert m[k]==w[k],k
    assert len(m['results'])==len(m['cases']) and all(a==b['actual'] for a,b in zip(m['results'],m['cases']))
    metal_summary={k:v for k,v in m.items() if k!='results'}
    metal_summary['duplicate_results_omitted']='Identical data retained in cases.actual;raw readback unchanged'
    save('portable-combat-metal',metal_summary,compact=True)
    m=metal_summary
    assert len(w['results'])==len(w['cases']) and all(a==b['actual'] for a,b in zip(w['results'],w['cases']))
    summary={k:v for k,v in w.items() if k!='results'}
    summary['duplicate_results_omitted']='Identical data remains in cases.actual and byte-exact Windows artifact'
    summary['retained_cuda_source_commit']='5a3ee26039dc031f98ccd34a9c3245ff606a8808'
    summary['current_source_compatible_verified_commit']=SOURCE
    summary['windows_execution_metadata_report']='portable-attack-flags-windows-execution.json'
    save('portable-combat-cuda',summary,compact=True)
    audit=load('portable-catalog-readiness');favorite=load('portable-favorite-readiness')
    assert audit['catalog_characters']==203 and audit['full_character_verified']==0 and favorite['passed']
    profiles=load('portable-roster-battles-metal');profile_count=len(profiles['cases'])
    common=dict(wire_abi='0x5045566F',mac_gates=37,unit_tests=251,core_programs=2950,positive_cases=2525,rejections=425,
        conditional_hp_contract_cases=20,native_projection_exact_profiles=124,known_native_hp_gap_profiles=2,attack_flag_native_cases=162,attack_flag_api_cases=8,target_state_native_cases=233,geometry_native_cases=190,
        probability_native_cases=92,real_profiles=profile_count,old_profiles_preserved=108,
        own_effect_preflight_passed=audit['own_effect_preflight_passed'],unadmitted_effects=sum(audit['issues'].values()),
        favorite_preflight_contexts=favorite['own_effect_preflight_contexts_passed'],favorite_all_four_stage_candidates=favorite['all_four_stages_preflight_characters'],
        full_character_verified=0,full_goal_complete=False,normal_ui_backend='cpu',
        initial_unlocalized_metal_finding_open=True,input_sha256=m['input_sha256'],output_sha256=m['output_sha256'])
    proof=dict(passed=True,source_commit=SOURCE,previous_proof_commit=PRIOR,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        **common,previous_2754_output_words_preserved=True,current_full_core_gpu_replayed=False,
        cuda_verification_mode='source-identical full core reuse plus20 new HP cases',windows_core_gpu_executions=1,windows_additional_component_gpu_executions=1,windows_total_gpu_executions_this_stage=2,additional_transfer_gpu_runs=0,
        windows_execution=execution,transfer=transfer,efficiency_decision=decision,production_change_adopted=False,benchmark_harness_first_attempt_failed=True,benchmark_first_control_raw_missing=True,benchmark_harness_finding='portable-attack-flags-benchmark-harness-finding.json',
        selected_candidate_requires_new_source_validation=decision['selected_for_adoption'])
    save('portable-attack-flags-validation',proof)
    checkpoint=dict(**common,verified_commit=SOURCE,previous_checkpoint=dict(proof_commit=PRIOR,report='Git baseline portable-combat-checkpoint.json'),
        batched_inputs=2950,input_words=86016,output_words=159744,metal_verified=True,cuda_verified=True,
        metal_report='portable-combat-metal.json',cuda_report='portable-combat-cuda.json',windows_report='windows-portable-attack-flags-v72.json',
        cuda_verification_mode='source-identical full core reuse plus20 new HP cases',windows_checks_this_stage=dict(core_gpu_executions=1,additional_component_gpu_executions=1,additional_transfer_gpu_runs=0),
        windows_execution_metadata='portable-attack-flags-windows-execution.json',
        source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_source_commit=SOURCE,windows_core_source_commit='5a3ee26039dc031f98ccd34a9c3245ff606a8808',windows_additional_component_source_commit=SOURCE,shared_gpu_source_bytes_equal=True,previous_proof_commit=PRIOR),
        validation_receipt='portable-attack-flags-validation.json',generated_source_comparison=transfer['normalized_generated_sha256'],
        existing_parity=m['attack_flag_existing_parity'],real_roster_profiles=profile_count,real_fixed_squad=8,
        weapon_only_metal_verified=203,real_equipment_initialization_squads=203,normal_ui_connected=False,
        catalog_characters=203,all_characters_supported=False,cpu_trace_used_as_gpu_input=False,missing_families=audit['missing_families'],
        regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},source_sha256=m['source_sha256'],validation_sha256=m['validation_sha256'],batch_layout=m['batch_layout'],
        current_full_metal_core_executed=True,current_full_cuda_core_executed=False,retained_source_identical_full_cuda_core_verified=True,retained_cuda_core_source_commit='5a3ee26039dc031f98ccd34a9c3245ff606a8808',current_source_actual_cuda_inputs=20,all_current_cuda_input_output_bytes_compared=True,
        initial_metal_finding_open=True,initial_metal_finding='portable-element-initial-core-finding.json',
        physical_attack_flags=dict(native_cases=162,raw_rejections=34,new_runtime_arrays=0,new_stat_slots=0,
            boolean_stat_ids=[36,52],presence_ignores_magnitude_and_scaling=True,skill_classification_separate=True,
            pellet_damage_captured_before_notifications=True,coordinate_piercing_certified=False),
        efficiency_decision='portable-attack-flags-efficiency-decision.json',
        next_work='Validate selected optimization before adoption if any;then remaining effects/world/all203 variants')
    save('portable-combat-checkpoint',checkpoint)
    names=['portable-attack-flags-validation','portable-combat-checkpoint','portable-combat-metal','portable-combat-cuda',
        'portable-attack-flags-broad-validation','portable-attack-flags-global-gates','portable-attack-flags-transfer-completed',
        'portable-attack-flags-windows-execution','portable-health-runtime-v73-execution','windows-portable-health-runtime-v73','portable-health-runtime-metal','portable-health-runtime-native','portable-conditional-hp-roster-diagnosis','portable-attack-flags-first-roster-metal','portable-attack-flags-roster-finding','portable-attack-flags-initial-gates-stopped','portable-health-runtime-first-fixture-finding','portable-attack-flags-timing-order','portable-attack-flags-benchmark',
        'portable-attack-flags-candidate-parity','portable-attack-flags-candidate-capture-check','portable-attack-flags-benchmark-harness-finding','portable-attack-flags-input-pack-check','portable-attack-flags-efficiency-decision','portable-attack-flags-existing-metal-parity',
        'portable-attack-flags-existing-cuda-parity','portable-attack-flags-prior-blocks','windows-portable-attack-flags-v72',
        'portable-attack-flags-native','portable-attack-flags-native-study','portable-attack-flags-metal','portable-favorite-readiness',
        'portable-burst-charge-speed-native-study','portable-catalog-readiness','portable-roster-battles-metal','portable-api-metal','portable-element-initial-core-finding']
    paths=[P/(n+'.json') for n in names]
    paths += [P/n for n in ['seal-attack-flag-gates.py','seal-attack-flag-cuda.py','seal-attack-flag-validation.py',
        'verify-health-runtime.py','verify-conditional-hp-roster-gap.py','characterize-burst-charge-speed.py','benchmark-attack-flags.py','decide-attack-flag-efficiency.py','verify-attack-flags-regression.py','run-attack-flag-gates.py','portable-attack-flags-first-benchmark-source.txt']]
    paths += [ROOT/'docs'/n for n in ['portable-attack-flags.md','portable-burst-charge-speed-design.md','portable-combat-runtime.md','mac-handoff.md','mac-migration.md']]
    save('portable-attack-flags-receipt',dict(passed=True,source_commit=SOURCE,
        native_study_historical_proof_commit=PRIOR,
        artifact_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}))
    print('Full Metal/CUDA physical flag evidence sealed;all203 goal remains incomplete')


if __name__=='__main__':main()
