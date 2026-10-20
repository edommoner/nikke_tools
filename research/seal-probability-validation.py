"""Seal completed probability evidence without changing the tested compute source."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'research'
SOURCE = '27a375145147a2d042c8c0e66fffdb908b2b1be3'
PRIOR = 'f2206ef4a32fb89ad9c4f2381bb9dbfa5ec711d1'


def load(name):
    return json.loads((P / (name + '.json')).read_text())


def save(name, value):
    (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    broad = load('portable-probability-broad-validation')
    transfer = load('portable-probability-transfer-completed')
    decision = load('portable-probability-efficiency-decision')
    metal, cuda = load('portable-combat-metal'), load('windows-portable-probability-v67')
    assert all(d['passed'] and d['source_commit'] == SOURCE for d in [broad, transfer, decision])
    assert broad['all_current_gates_passed'] and broad['mac_gates'] == 32
    assert transfer['artifact_transfer_complete'] and transfer['windows_execution_terminal']
    assert decision['efficiency_evaluated'] and not decision['production_change_adopted']
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=ROOT, check=True)
    assert metal['input_sha256'] == cuda['input_sha256'] and metal['output_sha256'] == cuda['output_sha256']
    summary = {k: v for k, v in cuda.items() if k != 'results'}
    summary['duplicate_results_omitted'] = 'Identical data remains in cases.actual and the byte-exact Windows artifact'
    save('portable-combat-cuda', summary)
    audit = load('portable-catalog-readiness')
    proof = dict(passed=True, source_commit=SOURCE, previous_proof_commit=PRIOR,
                 checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 wire_abi='0x5045566C', mac_gates=32, unit_tests=243,
                 core_programs=2280, positive_cases=1940, rejections=340,
                 probability_native_cases=92, probability_physical_4096_cases=5,
                 probability_api_cases=8, real_profiles=102, old_profiles_preserved=86,
                 previous_2182_output_words_preserved=True, transfer=transfer,
                 windows_gpu_executions=1, windows_pre_gpu_setup_failures=1,
                 windows_execution=cuda['execution'], windows_postcheck=cuda['postcheck'],
                 efficiency_decision=decision, production_change_adopted=False,
                 own_effect_preflight_passed=51, unadmitted_effects=sum(audit['issues'].values()),
                 full_character_verified=0, full_goal_complete=False, normal_ui_backend='cpu',
                 initial_unlocalized_metal_finding_open=True,
                 future_cpu_studies_not_gpu_validated=['core/range conditions', 'probability endpoint chains'],
                 report_directory_parent_fix='Research IO only after execution;both executed drivers are Git27a3751',
                 input_sha256=metal['input_sha256'], output_sha256=metal['output_sha256'])
    save('portable-probability-validation', proof)
    checkpoint = dict(wire_abi='0x5045566C', verified_commit=SOURCE,
        previous_checkpoint=dict(proof_commit=PRIOR, report='Git baseline portable-combat-checkpoint.json'),
        positive_cases=1940, rejections=340, batched_inputs=2280, input_words=86016, output_words=159744,
        metal_verified=True, cuda_verified=True, metal_report='portable-combat-metal.json',
        cuda_report='portable-combat-cuda.json', windows_report='windows-portable-probability-v67.json',
        windows_execution=cuda['execution'], windows_postcheck=cuda['postcheck'],
        windows_checks_this_stage=dict(gpu_executions=1, pre_gpu_setup_failures=1, additional_transfer_gpu_runs=0),
        source_provenance=dict(fixed_shared_source_commit=SOURCE, metal_core_source_commit=SOURCE,
                               windows_source_commit=SOURCE, previous_proof_commit=PRIOR),
        validation_receipt='portable-probability-validation.json',
        generated_source_comparison=transfer['normalized_generated_sha256'],
        existing_parity=metal['probability_existing_parity'], mac_gates=32, unit_tests=243,
        real_roster_profiles=102, real_fixed_squad=8, weapon_only_metal_verified=203,
        real_equipment_initialization_squads=203, normal_ui_connected=False, normal_ui_backend='cpu',
        catalog_characters=203, own_effect_preflight_passed=51, full_character_verified=0,
        all_characters_supported=False, full_goal_complete=False, cpu_trace_used_as_gpu_input=False,
        missing_families=audit['missing_families'],
        regressions={k: v for k, v in metal.items() if k.endswith('_cpu_regressions')},
        source_sha256=metal['source_sha256'], validation_sha256=metal['validation_sha256'],
        input_sha256=metal['input_sha256'], output_sha256=metal['output_sha256'], batch_layout=metal['batch_layout'],
        current_full_cuda_core_executed=True, initial_metal_finding_open=True,
        initial_metal_finding='portable-element-initial-core-finding.json',
        probability=dict(native_cases=92, state_words=2560, remaining_output_tail_words=512,
                         expected_mode_only=True, authored_condition_order=True, runtime_queries_skip_probability=True),
        efficiency_decision='portable-probability-efficiency-decision.json',
        next_work='Validate selected optimization before adoption if any;then remaining effects/world/all203 variants')
    save('portable-combat-checkpoint', checkpoint)
    names = ['portable-probability-validation', 'portable-combat-checkpoint', 'portable-probability-broad-validation',
             'portable-probability-global-gates', 'portable-probability-transfer-completed',
             'portable-probability-timing-order', 'portable-probability-candidate-parity',
             'portable-probability-benchmark', 'portable-probability-efficiency-decision',
             'portable-probability-existing-metal-parity', 'portable-probability-existing-cuda-parity',
             'portable-combat-metal', 'portable-combat-cuda', 'windows-portable-probability-v67']
    paths = [P / (n + '.json') for n in names]
    paths += [P / n for n in ['seal-probability-gates.py', 'seal-probability-cuda.py',
              'seal-probability-validation.py', 'benchmark-probability.py', 'decide-probability-efficiency.py']]
    paths += [ROOT / 'docs' / n for n in ['mac-handoff.md', 'mac-migration.md', 'portable-combat-runtime.md', 'portable-probability-design.md']]
    save('portable-probability-receipt', dict(passed=True, source_commit=SOURCE,
         artifact_sha256={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}))
    print('Probability fixed-source both-GPU proof/checkpoint sealed;full203 goal remains incomplete')


if __name__ == '__main__':
    main()
