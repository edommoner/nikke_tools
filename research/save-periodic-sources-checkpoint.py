"""Shared source lifecycle checkpoint; estimates stay explicit in both backends."""
import json,re
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=[f'research/periodic-sources-{suffix}.json' for suffix in ('native','ptx','unit','coverage','related-native','batch-native','owned-api','control-performance','counter-performance','source-api-baseline','pool-baseline')]
receipts=checked_receipts(reports)
for backend in ('native','ptx'):
    primary=receipts[f'research/periodic-sources-{backend}.json']
    assert primary['source_stable'] and not primary['cpu_trace_used_as_gpu_input'] and len(primary['cases'])==10
    assert all(r['passed'] for r in primary['cases'])
    assert primary['cases'][5]['expected']==[[32,1,1],[32,2,1]]
    assert all(r['estimated_parameters_warning'] for r in primary['cases'][7:])
unit=receipts['research/periodic-sources-unit.json'];assert unit['tests_run']==46 and not unit['skipped']
coverage=receipts['research/periodic-sources-coverage.json'];assert coverage['compile_only'] and coverage['supported']==182 and coverage['characters']==203 and len(coverage['new_character_favorite_stages'])==4
assert len(receipts['research/periodic-sources-related-native.json']['cases'])==25
assert receipts['research/periodic-sources-batch-native.json']['batch_squads']==8
assert receipts['research/periodic-sources-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
native,portable=read('app/detail_effects-sm86.json'),read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_periodic_sources_v56'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
workspace=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text())[1])
base='research/ports/v55-event-index-verified'
baselines=['research/event-index-control-after.json','research/event-index-counter-after.json']
measurements={}
for name,path in zip(('control','counter'),baselines):
    before=read(f'{base}/{path}');after=receipts[f'research/periodic-sources-{name}-performance.json']
    assert before['passed'] and after['candidates']==8 and after['cache_hits']==0
    semantic=lambda results:[{k:v for k,v in row.items() if k!='compute'} for row in results]
    assert semantic(before['results'])==semantic(after['results'])
    measurements[name]=dict(before_ms=before['wall_ms'],after_ms=after['wall_ms'],speedup=before['wall_ms']/after['wall_ms'])
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('app','detail_effects*'),('scripts','*.py'),('scripts','*.mjs'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'README.md','data/engine-effect-overrides.json'}
def previous(path):
    for root in (base,'research/ports/v54-target-counters-verified','research/ports/v53-typed-impacts-verified','research/ports/v52-resource-limits-verified'):
        p=ROOT/root/path
        if p.is_file():return p.read_bytes()
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports)
changed.update({'research/save-periodic-sources-checkpoint.py','research/checkpoint_receipts.py','research/verify-periodic-sources-coverage.py','research/periodic-sources-api-fixture.json','research/benchmark-normal-search.mjs','research/target-counters-api-fixture.json','research/verify-event-index-batch.py'})
changed.add('research/benchmark-periodic-source-pool.py')
checkpoint=dict(passed=True,generated_at=datetime.now(timezone.utc).isoformat(),objective_complete=False,abi=native['abi'],instruction_width=340,
    workspace_bytes_per_squad=workspace,workspace_added_bytes=workspace-1133304,archive_base=base,archive_kind='Delta over verified v55, resolving earlier v54/v53/v52 deltas',
    checks=dict(shared_clock_quantities=6,autonomous_squads=4,raw_squads=3,existing_shared_ordering_cases=25,existing_batch_squads=8,lightweight_methods=46,normal_owned_api=True),
    compile_only=dict(supported=182,catalog=203,new_character_favorite_inputs=4,not_all_squads_or_game_verification=True),reports=reports,measurements=measurements,
    scope='Owned slot resources, population clocks, atomic generation refresh, scoped source events and a legacy data adapter. CPU rewrite composition preserves earlier lifecycle edits. Legacy timings remain explicitly estimated.',
    efficiency_baselines=dict(owned_source8_ms=receipts['research/periodic-sources-source-api-baseline.json']['wall_ms'],authored_pool64_median_kernel_ms=receipts['research/periodic-sources-pool-baseline.json']['median_kernel_ms']),
    game_parameters_verified=False,remaining='After verification, attempt direct indexed periodic source lookup and measure against frozen baselines. Also21 standard compile-unaccepted characters, other effect/world families, component/target policies and game-rule evidence. All-character goal remains active.')
print(json.dumps(save_checkpoint('research/periodic-sources-checkpoint.json','research/ports/v56-periodic-sources-verified',checkpoint,changed)))
