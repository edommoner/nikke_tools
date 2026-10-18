"""Accept source-bound resource quantities and preserve the operation snapshot."""
import json
import re
from datetime import datetime, timezone
from checkpoint_receipts import ROOT, read, sha, checked_receipts, save_checkpoint

reports = [f'research/resource-limits-{n}.json' for n in ('native', 'ptx', 'unit',
    'related-native', 'owned-api', 'build-contract', 'state-layout', 'real-data-correction', 'api-performance')]
receipts = checked_receipts(reports)
for backend in ('native', 'ptx'):
    report = receipts[f'research/resource-limits-{backend}.json']
    assert report['source_stable'] and len(report['cases']) == 25
    assert all(row['passed'] for row in report['cases'])
    for row in report['cases'][:14]:
        assert row['remaining'] == row['expected_remaining']
        assert row['ammo_events'] == row['expected_ammo_events']
    for row in report['cases'][:2]:
        assert row['charge_event_spy_enabled'] and row['floor_did_not_emit_charge_events']
    nested = next(row for row in report['cases'] if row['name'] == 'nested-refill-does-not-change-parent-spend')
    assert all(row['spend_witness'] == 34 for row in nested['consumptions'])
    assert report['raw_floor_control']['passed'] and not report['raw_floor_control']['whole_character_gpu_accepted']
assert receipts['research/resource-limits-unit.json']['tests_run'] == 20
assert receipts['research/resource-limits-build-contract.json']['tests_run'] == 2
related = receipts['research/resource-limits-related-native.json']
assert related['tests_run'] == 1 and len(related['deferred_controls']) == 14
assert all(row['passed'] for row in related['deferred_controls'])
assert receipts['research/resource-limits-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
performance = receipts['research/resource-limits-api-performance.json']
assert performance['normal_api'] and performance['candidates'] == 8 and performance['cache_hits'] == 0
native, portable = read('app/detail_effects-sm86.json'), read('app/detail_effects-build.json')
assert native['abi'] == portable['abi'] == 'detail_resource_limits_v52'
assert native['source_sha256'] == portable['source_sha256'] == sha('app/detail_effects.cu')
assert native['binary_sha256'] == sha('app/detail_effects-sm86.cubin')
assert portable['ptx_sha256'] == sha('app/detail_effects.ptx')
workspace = int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);', (ROOT / 'app/detail_effects.ptx').read_text())[1])
assert workspace == 1103888
files = {str(p.relative_to(ROOT)).replace('\\', '/')
    for directory, pattern in [('app', '*.py'), ('app', 'detail_effects*'), ('app', '*.mjs'),
        ('scripts', '*.py'), ('scripts', '*.mjs'), ('tests', '*.py'), ('tests', '*.mjs'), ('docs', '*.md')]
    for p in (ROOT / directory).glob(pattern) if p.is_file()}
files.update(reports)
files.update({'server.mjs', 'README.md', 'package.json', 'data/engine-effect-overrides.json'})
files.update(f'research/{n}' for n in ('checkpoint_receipts.py', 'save-resource-limits-checkpoint.py',
    'verify-resource-related.py', 'resource-limits-contract.json', 'target-counter-dependency-audit.json',
    'benchmark-normal-search.mjs', 'damage-basis-additive-api-fixture.json',
    'upstream/nikke-calc-master/data/parsed_skills.json'))
checkpoint = dict(passed=True, generated_at=datetime.now(timezone.utc).isoformat(), objective_complete=False,
    abi=native['abi'], instruction_width=295, workspace_bytes_per_squad=workspace,
    scope='Shared per-operation consumption minimum and checked CPU data correction. Target-associated hit counter and whole possession character remain unfinished.',
    checks=dict(native_cases=25, portable_cases=25, unique_cases=25, independent_quantity_cases=14,
        new_squad_cases=2, reused_gauge_primitive_cases=9, selected_existing_deferred_controls=14,
        batch_squads=8, lightweight_methods=20, build_contract_methods=2, normal_owned_api=True),
    runtime_measurement=dict(candidates=8, wall_ms=performance['wall_ms'], baseline=performance['baseline'],
        interpretation='Single isolated measurement, no statistical or universal speed claim'),
    reports=reports,
    remaining='Explicit target/accepted-hit packets and target-counter lifetime/completion/cap-entry semantics; all remaining effect families. No all-character completion or new whole-character acceptance claim.')
print(json.dumps(save_checkpoint('research/resource-limits-checkpoint.json',
    'research/ports/v52-resource-limits-verified', checkpoint, files)))
