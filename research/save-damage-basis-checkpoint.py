"""Accept source-bound v50 receipts and archive an explicit file selection."""
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


reports = [f'research/damage-basis-{name}.json' for name in (
    'native', 'ptx', 'additive-owned-api', 'replacement-owned-api',
    'related-native', 'unit', 'build-contract', 'compile-migration',
    'api-performance', 'outlining-source-proof')]
receipts = {path: read(path) for path in reports}
for path, receipt in receipts.items():
    assert receipt['passed'], path
    for source, digest in receipt.get('source_sha256', {}).items():
        assert sha(source) == digest, (path, source)
for backend in ('native', 'ptx'):
    receipt = receipts[f'research/damage-basis-{backend}.json']
    assert receipt['source_stable'] and len(receipt['cases']) == 17
    assert all(row['passed'] for row in receipt['cases'])
    assert all(any(e['active'] for e in row['observations']) for row in receipt['cases'][12:])
    assert receipt['cases'][-1]['cover_both_branches_exercised']
for mode in ('additive', 'replacement'):
    assert receipts[f'research/damage-basis-{mode}-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
assert receipts['research/damage-basis-related-native.json']['tests_run'] == 2
assert receipts['research/damage-basis-unit.json']['tests_run'] == 4
assert receipts['research/damage-basis-build-contract.json']['tests_run'] == 2
migration = receipts['research/damage-basis-compile-migration.json']
assert migration['previous_programs_unchanged'] == 923
assert (migration['standard_accepted'], migration['favorite_accepted']) == (180, 714)
snapshot = read('research/damage-basis-compile-snapshot.json')
assert (snapshot['standard']['supported'], snapshot['favorite_accepted']) == (180, 714)
assert snapshot['raw_definition_sha256'] == sha('research/upstream/nikke-calc-master/data/parsed_skills.json')
native = read('app/detail_effects-sm86.json')
portable = read('app/detail_effects-build.json')
assert native['abi'] == portable['abi'] == 'detail_damage_basis_predicates_v50'
assert native['source_sha256'] == portable['source_sha256'] == sha('app/detail_effects.cu')
assert native['binary_sha256'] == sha('app/detail_effects-sm86.cubin')
assert portable['ptx_sha256'] == sha('app/detail_effects.ptx')
proof = receipts['research/damage-basis-outlining-source-proof.json']
assert proof['annotation_only'] and proof['unchanged_formula_and_layout']
assert proof['new_source_sha256'] == sha('app/detail_effects.cu')
workspace = int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);', (ROOT / 'app/detail_effects.ptx').read_text())[1])
assert workspace == 1103888
files = sorted({str(p.relative_to(ROOT)).replace('\\', '/')
    for directory, pattern in [('app', '*.py'), ('app', 'detail_effects*'),
        ('app', '*.mjs'), ('scripts', '*.py'), ('scripts', '*.mjs'),
        ('tests', '*.py'), ('tests', '*.mjs'), ('docs', '*.md')]
    for p in (ROOT / directory).glob(pattern) if p.is_file()}
    | {'server.mjs', 'README.md', 'package.json'})
additional = [f'research/{name}' for name in (
    'damage-basis-contract.json', 'damage-basis-compile-snapshot.json',
    'damage-basis-additive-api-fixture.json', 'damage-basis-replacement-api-fixture.json',
    'damage-basis-outlining-ptx-build.json', 'damage-basis-outlining-native-build.json',
    'damage-basis-resource-control.json', 'damage-basis-ptx-growth.json',
    'remaining-gpu-mechanic-gaps.json', 'target-context-evidence.json',
    'upstream/nikke-calc-master/data/parsed_skills.json',
    'profile-detail-build.py', 'benchmark-normal-search.mjs',
    'save-damage-basis-checkpoint.py')]
checkpoint = dict(generated_at=datetime.now(timezone.utc).isoformat(), passed=True,
    objective_complete=False, abi=native['abi'], workspace_bytes_per_squad=workspace,
    scope='HP attack basis, exclusive grouped ammo reduction, live undying and intact-cover activation predicates; no new character-name runtime branches',
    standard_accepted=180, standard_total=203, favorite_accepted=714, favorite_total=812,
    previous_programs_unchanged=923, new_standard=migration['new_standard'],
    checks=dict(native_cases=17, portable_cases=17, unique_new_cases=17,
        independent_quantities=12, actual_squads=5, normal_owned_api_modes=2,
        existing_related_methods=2, existing_related_squads=8,
        spec_and_boundary_tests=4, build_contract_tests=2),
    reports=reports, source_sha256={p: sha(p) for p in files + additional},
    remaining_standard=[r for r in snapshot['standard']['results'] if not r['supported']],
    test_selection='Shared quantity tables, active real skills, cover break/revival and both condition branches, whole-squad/RNG comparison as applicable, existing batch isolation and pellet ordering. No current full216 claim.',
    runtime_measurement=dict(candidates=8, wall_ms=4657.253, prior_ms=4813.2107,
        interpretation='Single isolated run; approximately retained speed, not a statistical speedup claim'),
    archive='research/ports/v50-damage-basis-verified')
target = ROOT / 'research/damage-basis-checkpoint.json'
target.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
archive = ROOT / checkpoint['archive']
archive.mkdir(exist_ok=False)
selection = sorted(set(files + additional + reports + ['research/damage-basis-checkpoint.json']))
for path in selection:
    destination = archive / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / path, destination)
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == sha(path)
print(json.dumps(dict(passed=True, files=len(selection), archive=str(archive))))
