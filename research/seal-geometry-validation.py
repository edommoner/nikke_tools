"""Seal fixed-source geometry evidence; optimization adoption needs its own proof."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'research'
SOURCE = '17decef851fbea0a300e16706c63ff6702e6e83f'
PRIOR = 'cd5762a8c95914a90d83d5e9552bf49414027a50'


def load(name):
    return json.loads((P / (name + '.json')).read_text())


def save(name, value, compact=False):
    options = dict(separators=(',', ':')) if compact else dict(indent=2)
    (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, **options) + '\n')


def main():
    broad = load('portable-geometry-broad-validation')
    transfer = load('portable-geometry-transfer-completed')
    decision = load('portable-geometry-efficiency-decision')
    metal = load('portable-combat-metal')
    cuda = load('windows-portable-geometry-v69')
    assert all(d['passed'] and d['source_commit'] == SOURCE for d in (broad, transfer, decision))
    assert broad['all_current_gates_passed'] and broad['mac_gates'] == 34
    assert transfer['artifact_transfer_complete'] and transfer['windows_execution_terminal']
    assert decision['efficiency_evaluated'] and not decision['production_change_adopted']
    assert metal['passed'] and cuda['passed']
    assert len(metal['cases']) == 2130 and len(metal['rejected_cases']) == 373
    assert len(metal['geometry_cpu_regressions']) == 190
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=ROOT, check=True)
    for key in ('input_sha256', 'output_sha256', 'source_sha256', 'validation_sha256'):
        assert metal[key] == cuda[key], key
    summary = {k: v for k, v in cuda.items() if k != 'results'}
    summary['duplicate_results_omitted'] = 'Identical data remains in cases.actual and the byte-exact Windows artifact'
    save('portable-combat-cuda', summary, compact=True)
    audit = load('portable-catalog-readiness')
    favorite = load('portable-favorite-readiness')
    assert favorite['passed']
    proof = dict(passed=True, source_commit=SOURCE, previous_proof_commit=PRIOR,
        checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        wire_abi='0x5045566D', mac_gates=34, unit_tests=246,
        core_programs=2503, positive_cases=2130, rejections=373,
        geometry_native_cases=190, geometry_physical_cases=8, geometry_api_cases=8,
        probability_native_cases=92, probability_physical_4096_cases=5,
        probability_api_cases=8, real_profiles=104, old_profiles_preserved=102,
        previous_2280_output_words_preserved=True, transfer=transfer,
        windows_gpu_executions=1, additional_transfer_gpu_runs=0,
        windows_execution=cuda['execution'], windows_postcheck=cuda['postcheck'],
        efficiency_decision=decision, production_change_adopted=False,
        selected_candidate_requires_new_source_validation=decision['selected_for_adoption'],
        own_effect_preflight_passed=52, unadmitted_effects=sum(audit['issues'].values()),
        full_character_verified=0, full_goal_complete=False, normal_ui_backend='cpu',
        initial_unlocalized_metal_finding_open=True,
        initial_geometry_observer_finding='portable-geometry-first-component-finding.json',
        current_full_core_gpu_replayed=False,
        input_sha256=metal['input_sha256'], output_sha256=metal['output_sha256'])
    save('portable-geometry-validation', proof)
    checkpoint = dict(wire_abi='0x5045566D', verified_commit=SOURCE,
        previous_checkpoint=dict(proof_commit=PRIOR, report='Git baseline portable-combat-checkpoint.json'),
        positive_cases=2130, rejections=373, batched_inputs=2503, input_words=86016, output_words=159744,
        metal_verified=True, cuda_verified=True, metal_report='portable-combat-metal.json',
        cuda_report='portable-combat-cuda.json', windows_report='windows-portable-geometry-v69.json',
        windows_execution=cuda['execution'], windows_postcheck=cuda['postcheck'],
        windows_checks_this_stage=dict(gpu_executions=1, additional_transfer_gpu_runs=0),
        source_provenance=dict(fixed_shared_source_commit=SOURCE, metal_core_source_commit=SOURCE,
                              windows_source_commit=SOURCE, previous_proof_commit=PRIOR),
        validation_receipt='portable-geometry-validation.json',
        generated_source_comparison=transfer['normalized_generated_sha256'],
        existing_parity=metal['geometry_existing_parity'], mac_gates=34, unit_tests=246,
        real_roster_profiles=104, real_fixed_squad=8, weapon_only_metal_verified=203,
        real_equipment_initialization_squads=203, normal_ui_connected=False, normal_ui_backend='cpu',
        catalog_characters=203, own_effect_preflight_passed=52, full_character_verified=0,
        all_characters_supported=False, full_goal_complete=False, cpu_trace_used_as_gpu_input=False,
        missing_families=audit['missing_families'],
        regressions={k: v for k, v in metal.items() if k.endswith('_cpu_regressions')},
        source_sha256=metal['source_sha256'], validation_sha256=metal['validation_sha256'],
        input_sha256=metal['input_sha256'], output_sha256=metal['output_sha256'], batch_layout=metal['batch_layout'],
        current_full_cuda_core_executed=True, initial_metal_finding_open=True,
        initial_metal_finding='portable-element-initial-core-finding.json',
        geometry=dict(native_cases=190, physical_cases=8, input_words=1592, remaining_input_tail_words=448,
                      core_literal_threshold=1, distance_slack='binary64 1e-9',
                      activation_uses_original_weapon=True, damage_uses_active_weapon=True,
                      authored_condition_order=True),
        efficiency_decision='portable-geometry-efficiency-decision.json',
        next_work='Validate selected optimization before adoption if any;then remaining effects/world/all203 variants')
    save('portable-combat-checkpoint', checkpoint)
    names = ['portable-geometry-validation', 'portable-combat-checkpoint', 'portable-geometry-broad-validation',
             'portable-geometry-global-gates', 'portable-geometry-transfer-completed',
             'portable-geometry-timing-order', 'portable-geometry-candidate-parity',
             'portable-geometry-benchmark', 'portable-geometry-efficiency-decision',
             'portable-geometry-existing-metal-parity', 'portable-geometry-existing-cuda-parity',
             'portable-geometry-first-component-finding', 'portable-geometry-first-metal',
             'portable-geometry-native', 'portable-combat-metal', 'portable-combat-cuda',
             'windows-portable-geometry-v69', 'portable-favorite-readiness', 'portable-not-core-native']
    paths = [P / (n + '.json') for n in names]
    paths += [P / n for n in ['seal-geometry-gates.py', 'seal-geometry-cuda.py',
              'seal-geometry-validation.py', 'benchmark-geometry.py', 'decide-geometry-efficiency.py',
              'characterize-not-core.py']]
    paths += [ROOT / 'docs' / n for n in ['mac-handoff.md', 'mac-migration.md', 'portable-combat-runtime.md', 'portable-probability-design.md']]
    save('portable-geometry-receipt', dict(passed=True, source_commit=SOURCE,
         artifact_sha256={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}))
    print('Geometry fixed-source both-GPU proof/checkpoint sealed;full203 goal remains incomplete')


if __name__ == '__main__':
    main()
