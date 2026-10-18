"""Source-bound acceptance of the common cast/landing operation."""
import re
import json
from datetime import datetime, timezone
from checkpoint_receipts import ROOT, sha, read, checked_receipts, save_checkpoint

assert read('research/deferred-attack-contract.json')['all_declared_interactions_verified'], 'Resolve query-scope interactions before accepting this mechanism'

reports = [f'research/deferred-attack-{name}.json' for name in
           ('native', 'ptx', 'unit', 'related-native', 'owned-api', 'compiler-isolation', 'build-contract', 'state-layout', 'query-scope-correction', 'api-performance')]
receipts = checked_receipts(reports)
for backend in ('native', 'ptx'):
    result = receipts[f'research/deferred-attack-{backend}.json']
    assert result['source_stable'] and len(result['cases']) == 22
    assert all(row['passed'] for row in result['cases'])
    for row in result['cases'][:8]:
        assert row['healing_before_landing'] == 0
        assert row['healing'] == row['expected_healing'] and row['same_frame_witness'] == 215 / 60
    latched = next(row for row in result['cases'] if row['name'] == 'latched-reference-and-gate')
    assert latched['observed']['hits'][0]['live_count'] == 2
assert receipts['research/deferred-attack-unit.json']['tests_run'] == 12
assert receipts['research/deferred-attack-build-contract.json']['tests_run'] == 2
assert receipts['research/deferred-attack-related-native.json']['tests_run'] == 4
assert receipts['research/deferred-attack-related-native.json']['copy_control']['passed']
assert len(receipts['research/deferred-attack-related-native.json']['basis_controls']) == 2
assert receipts['research/deferred-attack-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
assert receipts['research/deferred-attack-compiler-isolation.json']['character_still_rejected']
performance = receipts['research/deferred-attack-api-performance.json']
assert performance['normal_api'] and performance['candidates'] == 8 and performance['cache_hits'] == 0
native, portable = read('app/detail_effects-sm86.json'), read('app/detail_effects-build.json')
assert native['abi'] == portable['abi'] == 'detail_deferred_attack_v51'
assert native['source_sha256'] == portable['source_sha256'] == sha('app/detail_effects.cu')
assert native['binary_sha256'] == sha('app/detail_effects-sm86.cubin')
assert portable['ptx_sha256'] == sha('app/detail_effects.ptx')
workspace = int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);', (ROOT / 'app/detail_effects.ptx').read_text())[1])
assert workspace == 1103888
files = {str(p.relative_to(ROOT)).replace('\\', '/')
         for directory, pattern in [('app', '*.py'), ('app', 'detail_effects*'),
            ('app', '*.mjs'), ('scripts', '*.py'), ('scripts', '*.mjs'),
            ('tests', '*.py'), ('tests', '*.mjs'), ('docs', '*.md')]
         for p in (ROOT / directory).glob(pattern) if p.is_file()}
files |= {'server.mjs', 'README.md', 'package.json'}
files.update(reports)
files.update(f'research/{name}' for name in ('checkpoint_receipts.py', 'save-deferred-attack-checkpoint.py',
    'deferred-attack-contract.json', 'deferred-attack-character-evidence.json', 'damage-basis-additive-api-fixture.json',
    'verify-deferred-related.py',
    'benchmark-normal-search.mjs',
    'upstream/nikke-calc-master/data/parsed_skills.json'))
checkpoint = dict(generated_at=datetime.now(timezone.utc).isoformat(), passed=True,
    objective_complete=False, abi=native['abi'], workspace_bytes_per_squad=workspace,
    scope='Shared explicit full-burst landing scheduling, not whole new character acceptance or own in-game animation verification',
    checks=dict(native_cases=22, portable_cases=22, unique_cases=22,
        independent_quantities=8, new_squad_cases=10, reused_legacy_cases=4,
        existing_related_methods=4, copy_control=1, basis_controls=2, spec_boundary_methods=12,
        build_contract_methods=2, normal_owned_api=True),
    compile_scope='The v50 snapshot180/203 and714/812 was not recomputed as a new all-character acceptance claim. Possession character remains rejected.',
    runtime_measurement=dict(candidates=8, wall_ms=performance['wall_ms'], baseline=performance['baseline'],
        interpretation='Single isolated run after correctness; no statistical or universal speedup claim'),
    reports=reports, remaining='Possession, resource floor, target-scoped capture counters and all remaining common families; all-character goal stays active.')
print(json.dumps(save_checkpoint('research/deferred-attack-checkpoint.json',
    'research/ports/v51-deferred-attack-verified', checkpoint, files)))
