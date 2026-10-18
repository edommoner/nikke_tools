"""Accept the measured lookup optimization only after the shared source proof."""
import json,re
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=[f'research/source-index-{suffix}.json' for suffix in ('native','ptx','unit','coverage','related-native','batch-native','owned-api','control-performance','counter-performance','source-api-performance','pool-performance')]
receipts=checked_receipts(reports)
for backend in ('native','ptx'):
    primary=receipts[f'research/source-index-{backend}.json']
    assert primary['source_stable'] and len(primary['cases'])==10 and all(r['passed'] for r in primary['cases'])
    assert not primary['cpu_trace_used_as_gpu_input']
assert receipts['research/source-index-unit.json']['tests_run']==46
assert receipts['research/source-index-coverage.json']['supported']==182
assert len(receipts['research/source-index-related-native.json']['cases'])==25
assert receipts['research/source-index-batch-native.json']['batch_squads']==8
assert receipts['research/source-index-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
base='research/ports/v56-periodic-sources-verified'
pool_before=read(f'{base}/research/periodic-sources-pool-baseline.json');pool_after=receipts['research/source-index-pool-performance.json']
assert pool_before['program_sha256']==pool_after['program_sha256'] and pool_before['results']==pool_after['results']
assert len(pool_after['samples'])==3 and pool_after['median_kernel_ms']<pool_before['median_kernel_ms']
measurements=dict(pool64=dict(before_median_kernel_ms=pool_before['median_kernel_ms'],after_median_kernel_ms=pool_after['median_kernel_ms'],speedup=pool_before['median_kernel_ms']/pool_after['median_kernel_ms']))
semantic=lambda results:[{k:v for k,v in row.items() if k!='compute'} for row in results]
for kind,baseline in (('source-api','source-api-baseline'),('control','control-performance'),('counter','counter-performance')):
    before=read(f'{base}/research/periodic-sources-{baseline}.json');after=receipts[f'research/source-index-{kind}-performance.json']
    assert semantic(before['results'])==semantic(after['results']) and before['cache_hits']==after['cache_hits']==0 and after['candidates']==8
    fixture='research/periodic-sources-api-fixture.json' if kind=='source-api' else 'research/target-counters-api-fixture.json' if kind=='counter' else 'research/base-copy-api-fixtures.json'
    for shared in (fixture,'research/benchmark-normal-search.mjs'):assert before['source_sha256'][shared]==after['source_sha256'][shared]
    measurements[kind]=dict(before_ms=before['wall_ms'],after_ms=after['wall_ms'],speedup=before['wall_ms']/after['wall_ms'])
native,portable=read('app/detail_effects-sm86.json'),read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_source_index_v57'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
workspace=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text())[1]);assert workspace==1153816
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('app','detail_effects*'),('scripts','*.py'),('scripts','*.mjs'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'README.md','data/engine-effect-overrides.json'}
def previous(path):
    for root in (base,'research/ports/v55-event-index-verified','research/ports/v54-target-counters-verified','research/ports/v53-typed-impacts-verified','research/ports/v52-resource-limits-verified'):
        p=ROOT/root/path
        if p.is_file():return p.read_bytes()
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports)
changed.update({'research/save-source-index-checkpoint.py','research/checkpoint_receipts.py','research/benchmark-periodic-source-pool.py','research/benchmark-normal-search.mjs','research/verify-periodic-sources-coverage.py','research/verify-event-index-batch.py','research/periodic-sources-api-fixture.json','research/target-counters-api-fixture.json'})
checkpoint=dict(passed=True,generated_at=datetime.now(timezone.utc).isoformat(),objective_complete=False,
    abi=native['abi'],instruction_width=340,workspace_bytes_per_squad=workspace,workspace_added_bytes=1280,archive_base=base,
    checks=dict(shared_primary_cases=10,existing_ordering_cases=25,existing_batch_squads=8,lightweight_methods=46,normal_owned_api=True),reports=reports,
    measurements=measurements,scope='Efficiency attempt after verified v56 common operation. Bounded direct owner/name resource index; lazy initialization preserves no-source path. No numeric/clock/lifecycle changes.',
    measurement_scope='Authored pool64 GPU kernel median of3 warm runs; source-owned and no-source normal API batches are single uncached measurements. Not a universal gameplay speedup.',
    compile_only=dict(supported=182,catalog=203),game_parameters_verified=False,
    remaining='21 standard compile-unaccepted characters and other effect/world families and game-rule evidence. Verify each new common operation, then attempt efficiency improvements. After all-character support, perform another end-to-end whole-system efficiency review. Goal remains active.')
print(json.dumps(save_checkpoint('research/source-index-checkpoint.json','research/ports/v57-source-index-verified',checkpoint,changed)))
