"""Record charge-control evidence with explicit scope and source fingerprints."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def raw(path):
    data = (ROOT / path).read_bytes()
    return data.decode('utf-16') if data.startswith(b'\xff\xfe') else data.decode('utf-8-sig')


def read(path):
    return json.loads(raw(path))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, data):
    (ROOT / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


main = read('research/detail-control-verification.json')
api = read('research/detail-control-api-verification.json')
ui = read('research/detail-control-ui-verification.json')
assert ui['passed'] and ui['operation_label_correct'] and sum(ui['member_damage']) == ui['total_damage']
for report in (main, api):
    assert report['passed']
    for path, digest in report['source_sha256'].items():
        assert sha(path) == digest, path
assert not main['cpu_trace_used_as_gpu_input']
counts = {backend: len(result['cases']) for backend, result in main['backends'].items()}
assert counts == {'native': 28, 'ptx': 28}, counts
for key in ('normal_compare_gpu', 'cpu_verification', 'board_gpu', 'cache_separated', 'unsupported_cpu_fallback', 'shooting_modes_separate'):
    assert api[key], key
regression = raw('research/detail-control-tests.log')
match = re.search(r'Ran (\d+) tests in ([\d.]+)s', regression)
assert match and int(match[1]) == 102 and '\nOK' in regression and 'skipped=' not in regression
node = raw('research/detail-control-node-tests.log')
assert 'pass 20' in node and 'fail 0' in node
coverage = read('research/detail-coverage-control.json')
assert coverage['supported'] == 105
previous_coverage = read('research/detail-coverage-health-reload.json')
previous_names = {r['character'] for r in previous_coverage['results'] if r['supported']}
new_names = [r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in previous_names]
assert len(new_names) == 2
audit = read('research/detail-all-effects-audit.json')
assert audit['accepted_contexts'] == 408
old = read('research/detail-health-reload-checkpoint.json')
upstream = {p: h for p, h in old['source_sha256'].items() if p.startswith('research/upstream/')}
for path, digest in upstream.items():
    assert sha(path) == digest, path
files = set(main['source_sha256']) | set(api['source_sha256']) | {
    'tests/test_detail_control.py', 'research/detail-control-tests.log',
    'research/detail-control-node-tests.log', 'research/detail-control-ui-fixture.json',
    'research/detail-coverage-control.json', 'research/detail-charge-control-cpu-references.json',
    'research/detail-control-ui-verification.json',
    'research/detail-control-verification.json', 'research/detail-control-api-verification.json',
}
catalog = read('research/detail-catalog-verification.json')
catalog_current = catalog['passed'] and all(sha(p) == h for p, h in catalog['source_sha256'].items())
if catalog_current:
    assert catalog['compiled_characters'] == 105 and len(catalog['cases']) == 210
    assert {b: sum(c['backend'] == b for c in catalog['cases']) for b in ('native', 'ptx')} == {'native': 105, 'ptx': 105}
    files.add('research/detail-catalog-verification.json')
now = datetime.now(timezone.utc).isoformat()
checkpoint = {
    'generated_at': now, 'passed': True, 'objective_complete': False,
    'abi': 'detail_control_v14', 'effect_row_width': 256, 'character_row_width': 160,
    'compiled_characters': 105, 'catalog_characters': 203,
    'new_characters': new_names,
    'favorite_contexts_compiled': 408, 'favorite_contexts_total': 812,
    'compile_acceptance_is_not_parity': True,
    'mechanics_cases_by_backend': counts, 'mechanics_cases': sum(counts.values()),
    'python_tests_passed': 102, 'python_test_seconds': float(match[2]), 'node_tests_passed': 20,
    'normal_api_total': api['total'], 'workspace_bytes_per_squad': api['compute']['workspace_bytes'],
    'current_catalog_verified': catalog_current,
    'catalog_cases': len(catalog['cases']) if catalog_current else None,
    'cpu_trace_used_as_gpu_input': False,
    'scope': 'Static enemy expected-value full five-member battles. Hold/tap/camera arbitration, charge state and supported real controls on native/PTX, owned equipment/stat deltas through normal API. Not every character, control grammar, favorite stage or combination.',
    'reports': ['research/detail-control-verification.json', 'research/detail-control-api-verification.json', 'research/detail-control-ui-verification.json', 'research/detail-control-tests.log'],
    'source_sha256': {**{p: sha(p) for p in sorted(files)}, **upstream},
}
write('research/detail-control-checkpoint.json', checkpoint)
progress = read('research/detail-expansion-next.json')
progress.update(generated_at=now, objective_complete=False)
progress.pop('current_work', None)
progress.pop('next_charge_control_reference', None)
progress['current_checkpoint_path'] = 'research/detail-control-checkpoint.json'
progress['new_characters'] = new_names
progress['layout'].update(EW=256, CW=160, workspace_bytes=checkpoint['workspace_bytes_per_squad'])
progress['layout'].update(
    CW40_43='click count, sequence count, static camera mask, control mode',
    CW48_143='8 click entries of 12 fields', CW144_159='8 absolute hold sequence entries',
    events39_40='charge hold threshold/count and non-full-charge fire',
    conditions29_30='during_charge and focusing', query108='final charge/control state output only',
)
progress['completed_control_semantics'] = [
    'GPU owns hold/release, partial shots, tap/periodic full-charge, operation priority and preemption',
    'Charge state separate from weapon phase; weapon changes, forced reload and pending auto reload preserve CPU event order',
    'Camera ownership follows CPU same-frame buff cache; first normal landed shot invalidates cache',
    'Shooting policy is independent from burst policy in CPU/GPU preparation and saved UI settings',
]
progress['current_checkpoint'] = {
    'implemented': progress['completed_control_semantics'],
    'reports': checkpoint['reports'], 'scope': checkpoint['scope'],
    'remaining': 'All-character and all-special-effect migration is incomplete',
}
progress['next_implementation'] = [
    'Expand active-slot/definition/condition/stat-cache capacities and preserve lazy target history across slot reuse',
    'Remaining anchored sequences, cover/reload cancel/aim grammar and unsupported charge-adjacent effects',
    'Named skill hit/crit and team-hit original-owner versus attacker contexts',
    'Incoming damage/HP/down/revive, live bosses/parts/projectiles, variable burst stages/reentry and accumulated burst gauge',
    'Outgoing healing, upstream omitted healing/Assister cubes, remaining shield/cover/projectile effects and skill copy',
    'All rejected characters, favorite contexts and random real-character combinations need implementation and independent parity',
]
progress['checkpoint'].update(
    compile_coverage=105, previous=103, coverage_path='research/detail-coverage-control.json',
    favorite_contexts_accepted=408,
    workspace_abi='detail_control_v14', workspace_bytes_per_squad=checkpoint['workspace_bytes_per_squad'],
    python_tests_passed=102, node_tests_passed=20,
    control_cases_total=checkpoint['mechanics_cases'], control_report=checkpoint['reports'][0],
    normal_api_control_gpu_verified=True, normal_api_control_total=api['total'],
    current_catalog_verified=catalog_current,
    accepted_catalog_characters=105 if catalog_current else None,
    accepted_catalog_full_squad_cases=checkpoint['catalog_cases'],
    regression_status='passed: Python102, Node20, charge-control56 native/PTX, normal API equipment/delta/control and browser UI; catalog current=' + str(catalog_current),
    historical_reports_note='Current control evidence: detail-control-checkpoint.json; older reports are historical unless source hashes match.',
)
progress['control_remaining'] = ['Anchored control sequences, cover/reload cancel and aim grammar', 'Other rejected raw effects and all-character/favorite/combinations parity', 'Incoming damage, live enemy/parts and upstream omitted mechanics']
write('research/detail-expansion-next.json', progress)
print(json.dumps({k: v for k, v in checkpoint.items() if k != 'source_sha256'}, ensure_ascii=True))
