"""Check the completed fixed-source Mac gates independently of CUDA evidence."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'research'
SOURCE = '795a9e5b684796b3b6a2fb9b59546e60401a5503'
PRIOR = '3f6342fcee8d5d2773a89307597dbd5bd184f01e'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())


def main():
    gates = load('portable-target-states-global-gates')
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 35 and gates['source_commit'] == SOURCE
    assert all(row['exit_code'] == 0 and row['source_commit'] == SOURCE for row in gates['gates'])
    subprocess.run(['git', 'diff', '--exit-code', SOURCE, '--', 'app', 'scripts', 'gpu', 'tests'], cwd=ROOT, check=True)
    core = load('portable-combat-metal')
    assert core['passed'] and core['gpu_execution_verified'] and core['backend'] == 'metal'
    assert len(core['cases']) == 2363 and len(core['rejected_cases']) == 391 and len(core['probability_cpu_regressions']) == 92 and len(core['geometry_cpu_regressions']) == 190 and len(core['target_state_cpu_regressions']) == 233
    parity = core['target_state_existing_parity']
    assert parity['passed'] and parity['prior_inputs'] == 2503 and parity['current_inputs'] == 2754
    assert parity['source_commit'] == SOURCE and parity['compute_worktree_clean'] and not parity['gpu_execution_reused']
    assert not parity['changed'] and parity['all_old_output_words_equal'] and parity['no_output_normalization'] and parity['no_gpu_retry']
    for group in ['source_sha256', 'validation_sha256']:
        for path, expected in core[group].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
            assert hashlib.sha256(subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT)).hexdigest() == expected, path
    roster = load('portable-roster-battles-metal')
    assert roster['passed'] and len(roster['cases']) == 108 and all(row['passed'] for row in roster['cases'])
    prior = json.loads(subprocess.check_output(['git', 'show', PRIOR + ':research/portable-roster-battles-metal.json'], cwd=ROOT))
    assert len(prior['cases']) == 104
    lookup = {(c['character'], c['grown']): c for c in roster['cases']}
    for old in prior['cases']:
        current = lookup[old['character'], old['grown']]
        assert all(k == 'cpu_reference_wall_seconds' or old.get(k) == current.get(k) for k in set(old) | set(current)), old['character']
    unit_groups = {}
    for name, count in {'unit': 249, 'staged-native': 9, 'source-native': 6, 'native-mode-spec': 4,
                        'native-mode-input': 3, 'reference-rewrite': 3}.items():
        row = next(r for r in gates['gates'] if r['name'] == name)
        text = Path(row['log']).read_text()
        assert f'Ran {count} tests' in text and text.rstrip().endswith('OK')
        unit_groups[name] = dict(tests=count, output=text)
    native = load('portable-target-states-native')
    assert native['passed'] and len(native['cases']) == 233
    api = load('portable-api-metal')
    assert api['passed'] and len(api['target_state_execution']) == 10 and len(api['geometry_execution']) == 8 and len(api['probability_execution']) == 8 and len(api['element_override_execution']) == 9
    audit = load('portable-catalog-readiness')
    assert audit['own_effect_preflight_passed'] == 54 and audit['full_character_verified'] == 0 and sum(audit['issues'].values()) == 345
    report = dict(passed=True, all_current_gates_passed=True, source_commit=SOURCE, previous_proof_commit=PRIOR,
                  checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), mac_gates=35,
                  core_programs=2754, positive_cases=2363, rejections=391, target_state_native_cases=233, geometry_native_cases=190, probability_native_cases=92,
                  geometry_physical_cases=8, probability_physical_4096_cases=5, target_state_api_cases=10, geometry_api_cases=8, probability_api_cases=8, unit_tests=249, unit_groups=unit_groups,
                  real_profiles=108, old_profiles_preserved=104, own_effect_preflight_passed=54,
                  initial_unlocalized_metal_finding_open=True, full_character_verified=0, full_goal_complete=False,
                  efficiency_evaluated=False, cuda_evidence_report='portable-target-states-transfer-completed.json',
                  scope='Completed fixed-source Mac gates only;CUDA evidence is sealed separately')
    (REPORTS / 'portable-target-states-broad-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('35 fixed-source Mac gates,249 units,108 profiles and all2754 core inputs verified')


if __name__ == '__main__':
    main()
