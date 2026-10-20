"""Check the completed fixed-source Mac gates independently of CUDA evidence."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'research'
SOURCE = '7492d8b191471f820989dc760bc4adc91494cf6a'
PRIOR = '13c9bdf734fde4325db7376165fcc904b549a242'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())


def main():
    gates = load('portable-attack-flags-global-gates')
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 37 and gates['source_commit'] == SOURCE
    assert all(row['exit_code'] == 0 and row['source_commit'] == SOURCE for row in gates['gates'])
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=ROOT, check=True)
    core = load('portable-combat-metal')
    assert core['passed'] and core['gpu_execution_verified'] and core['backend'] == 'metal'
    assert len(core['cases']) == 2525 and len(core['rejected_cases']) == 425 and len(core['probability_cpu_regressions']) == 92 and len(core['geometry_cpu_regressions']) == 190 and len(core['target_state_cpu_regressions']) == 233
    parity = core['attack_flag_existing_parity']
    assert parity['passed'] and parity['prior_inputs'] == 2754 and parity['current_inputs'] == 2950
    assert parity['source_commit'] == SOURCE and parity['compute_worktree_clean'] and not parity['gpu_execution_reused']
    assert not parity['changed'] and parity['all_old_output_words_equal'] and parity['no_output_normalization'] and parity['no_gpu_retry']
    for group in ['source_sha256', 'validation_sha256']:
        for path, expected in core[group].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
            assert hashlib.sha256(subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT)).hexdigest() == expected, path
    roster = load('portable-roster-battles-metal')
    assert roster['passed'] and len(roster['cases']) == 126 and all(row['passed'] for row in roster['cases'])
    prior = json.loads(subprocess.check_output(['git', 'show', PRIOR + ':research/portable-roster-battles-metal.json'], cwd=ROOT))
    assert len(prior['cases']) == 108
    lookup = {(c['character'], c['grown']): c for c in roster['cases']}
    for old in prior['cases']:
        current = lookup[old['character'], old['grown']]
        assert all(k == 'cpu_reference_wall_seconds' or old.get(k) == current.get(k) for k in set(old) | set(current)), old['character']
    initial=load('portable-attack-flags-first-roster-metal')
    assert len(initial['cases'])==126 and len(roster['known_cpu_difference_cases'])==2
    for old,current in zip(initial['cases'],roster['cases']):
        assert old['character']==current['character'] and old['grown']==current['grown']
        assert old['gpu_result']==current['gpu_result'] and old['native_reference']==current['native_reference']
        if old['passed']:assert old['differences']==current['differences']==[]
        else:assert current['known_cpu_difference']['original_native_differences']==old['differences']
    for batch in roster['gpu_batches']:
        captured=batch['captured']
        for field,hash_key in [('input_path','input_sha256'),('readback_path','output_sha256')]:
            assert hashlib.sha256(Path(captured[field]).read_bytes()).hexdigest()==batch[hash_key]
    conditional=load('portable-health-runtime-metal')
    assert conditional['passed'] and conditional['gpu_execution_verified'] and len(conditional['cases'])==20
    unit_groups = {}
    for name, count in {'unit': 251, 'staged-native': 9, 'source-native': 6, 'native-mode-spec': 4,
                        'native-mode-input': 3, 'reference-rewrite': 3}.items():
        row = next(r for r in gates['gates'] if r['name'] == name)
        text = Path(row['log']).read_text()
        assert f'Ran {count} tests' in text and text.rstrip().endswith('OK')
        unit_groups[name] = dict(tests=count, output=text)
    native = load('portable-attack-flags-native')
    assert native['passed'] and len(native['cases']) == 162
    api = load('portable-api-metal')
    assert len(core['attack_flag_cpu_regressions']) == 162
    assert api['passed'] and len(api['attack_flag_execution']) == 8 and len(api['target_state_execution']) == 10 and len(api['geometry_execution']) == 8 and len(api['probability_execution']) == 8 and len(api['element_override_execution']) == 9
    audit = load('portable-catalog-readiness')
    assert audit['own_effect_preflight_passed'] == 63 and audit['full_character_verified'] == 0 and sum(audit['issues'].values()) == 310
    report = dict(passed=True, all_current_gates_passed=True, source_commit=SOURCE, previous_proof_commit=PRIOR,
                  checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), mac_gates=37,
                  core_programs=2950, positive_cases=2525, rejections=425, attack_flag_native_cases=162, attack_flag_api_cases=8, target_state_native_cases=233, geometry_native_cases=190, probability_native_cases=92,
                  geometry_physical_cases=8, probability_physical_4096_cases=5, target_state_api_cases=10, geometry_api_cases=8, probability_api_cases=8, unit_tests=251, unit_groups=unit_groups,
                  conditional_hp_contract_cases=20, native_projection_exact_profiles=124, known_native_hp_gap_profiles=2, real_profiles=len(roster['cases']), old_profiles_preserved=108, own_effect_preflight_passed=audit['own_effect_preflight_passed'],
                  initial_unlocalized_metal_finding_open=True, full_character_verified=0, full_goal_complete=False,
                  efficiency_evaluated=False, cuda_evidence_report='portable-attack-flags-transfer-completed.json',
                  scope='Completed fixed-source Mac gates only;CUDA evidence is sealed separately')
    (REPORTS / 'portable-attack-flags-broad-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('37 fixed-source Mac gates,251 units and all2950 core inputs verified; real profiles',len(roster['cases']))


if __name__ == '__main__':
    main()
