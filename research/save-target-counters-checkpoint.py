"""Accept source-bound common counters and bounded real capture data migration."""
import json,re
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=[f'research/target-counters-{suffix}.json' for suffix in
    ('native','ptx','unit','related-native','owned-api','coverage','api-performance','counter-performance')]
receipts=checked_receipts(reports)
for backend in ('native','ptx'):
    report=receipts[f'research/target-counters-{backend}.json']
    assert report['source_stable'] and not report['cpu_trace_used_as_gpu_input'] and len(report['cases'])==18
    assert all(r['passed'] for r in report['cases'])
    assert report['cases'][11]['damage']==1000 and report['cases'][11]['captures']==3
    assert report['cases'][12]['completions']==2 and report['cases'][12]['child_resource']==1
    squads=report['cases'][13:]
    assert [(r['counter_frames'],r['completed']) for r in squads]==[(482,12),(482,1),(5402,15),(482,2),(482,2)]
    raw=squads[2];assert raw['overflows'][0]['capture_number']==14 and raw['enemy_code']=='작열' and raw['element_matches_enemy']
    assert all(o['resource']==13 for o in raw['overflows'])
    assert raw['element_bonus_at_least_four']>=raw['element_bonus_below_four']+30.23-1e-9
    assert any(c['effect']=='13 고스트' for c in squads[3]['cast_effects'])
    assert any(c['effect']=='13 고스트 3' for c in squads[4]['cast_effects'])
unit=receipts['research/target-counters-unit.json'];assert unit['tests_run']==38 and not unit['skipped']
related=receipts['research/target-counters-related-native.json'];assert related['batch_squads']==8 and len(related['cases'])==7 and not related['skipped']
assert receipts['research/target-counters-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
assert receipts['research/target-counters-owned-api.json']['model_warning_assertion_enabled']
coverage=receipts['research/target-counters-coverage.json'];assert coverage['compile_only'] and coverage['supported']==181 and coverage['characters']==203
for name in ('api-performance','counter-performance'):
    performance=receipts[f'research/target-counters-{name}.json'];assert performance['candidates']==8 and performance['cache_hits']==0
native,portable=read('app/detail_effects-sm86.json'),read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_target_counters_v54'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
workspace=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text())[1]);assert workspace==1128952
base='research/ports/v53-typed-impacts-verified'
# v53 is itself a delta over v52. Compare against that resolved base chain.
older='research/ports/v52-resource-limits-verified'
inventory={str(p.relative_to(ROOT)).replace('\\','/') for directory,pattern in
    [('app','*.py'),('app','detail_effects*'),('scripts','*.py'),('scripts','*.mjs'),('tests','*.py'),('docs','*.md')]
    for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'README.md','data/engine-effect-overrides.json'}
def previous(path):
    for root in (base,older):
        p=ROOT/root/path
        if p.is_file():return p.read_bytes()
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports)
changed.update({'research/save-target-counters-checkpoint.py','research/checkpoint_receipts.py','research/verify-target-counter-related.py',
    'research/verify-target-counter-unit.py','research/benchmark-normal-search.mjs','research/target-counters-api-fixture.json'})
checkpoint=dict(passed=True,generated_at=datetime.now(timezone.utc).isoformat(),objective_complete=False,
    abi=native['abi'],instruction_width=304,workspace_bytes_per_squad=workspace,workspace_added_bytes=workspace-1108376,
    archive_base=base,archive_kind='Delta over verified v53, which overlays verified v52',
    checks=dict(unique_primary_cases=18,native_primary_cases=18,portable_primary_cases=18,authored_counter_cases=13,
        autonomous_squads=5,raw_capture_squads=3,lightweight_methods=38,existing_batch_squads=8,existing_dependency_controls=7,normal_owned_api=True),
    reports=reports,compile_only=dict(supported=181,catalog=203,new_bounded_recipe='일레그 : 붐 앤 쇼크',not_all_squads_or_game_correctness=True),
    measurements=dict(control8_ms=receipts['research/target-counters-api-performance.json']['wall_ms'],
        counter8_ms=receipts['research/target-counters-counter-performance.json']['wall_ms'],scope='Uncached normal API baselines; GPU interval also includes packing/transfer/readback, not a pure kernel profiler'),
    scope='Common physical-actor hit counters with explicit credit/ownership/refresh/death policies, and bounded single-body capture recipe. Known ammo and cap-entry approximations corrected as data.',
    remaining='All-character goal remains active:22 standard compile-unaccepted characters, remaining effect/world families, component/logical-target capture binding and special hit policy evidence. No blanket game-correctness claim.')
print(json.dumps(save_checkpoint('research/target-counters-checkpoint.json','research/ports/v54-target-counters-verified',checkpoint,changed)))
