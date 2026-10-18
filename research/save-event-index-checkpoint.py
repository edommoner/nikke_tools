"""Source-bound dispatch proof and measured normal-path performance delta."""
import json,re
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint

reports=[f'research/event-index-{suffix}.json' for suffix in (
    'layouts-native','layouts-ptx','regressions-native','regressions-ptx','counters-native','counters-ptx',
    'unit','batch-native','owned-api','control-after','counter-after')]
receipts=checked_receipts(reports)
for backend in ('native','ptx'):
    layout=receipts[f'research/event-index-layouts-{backend}.json']
    assert layout['source_stable'] and layout['standard_supported']==181 and layout['accepted_contexts']==718
    assert layout['distinct_layouts']==layout['gpu']['layouts']==221 and layout['synthetic_layouts']==2
    regression=receipts[f'research/event-index-regressions-{backend}.json']
    assert regression['source_stable'] and len(regression['cases'])==25 and all(r['passed'] for r in regression['cases'])
    counter=receipts[f'research/event-index-counters-{backend}.json']
    assert counter['source_stable'] and len(counter['cases'])==(18 if backend=='native' else 13)
    assert all(r['passed'] for r in counter['cases'])
assert receipts['research/event-index-unit.json']['tests_run']==40
assert receipts['research/event-index-batch-native.json']['batch_squads']==8
assert receipts['research/event-index-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
native,portable=read('app/detail_effects-sm86.json'),read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_event_index_v55'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
workspace=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text())[1])
assert workspace==1133304
base='research/ports/v54-target-counters-verified'
baselines=[f'research/event-index-{kind}-timing-before.json' for kind in ('control','counter')]
measurements={}
for kind,path in zip(('control','counter'),baselines):
    before=read(path);after=receipts[f'research/event-index-{kind}-after.json']
    assert before['passed'] and before['cache_hits']==after['cache_hits']==0 and before['candidates']==after['candidates']==8
    # These are deliberately historical measurements, not current-source receipts.
    for artifact in ('app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json'):
        assert before['source_sha256'][artifact]==sha(f'{base}/{artifact}')
    assert after['baseline']==path
    project=lambda results:[{k:v for k,v in row.items() if k!='compute'} for row in results]
    assert project(before['results'])==project(after['results'])
    assert after['wall_ms']<before['wall_ms']
    old_kernel=before['results'][0]['compute']['timings_ms']['kernel_cuda']
    new_kernel=after['results'][0]['compute']['timings_ms']['kernel_cuda']
    assert new_kernel<old_kernel
    measurements[kind]=dict(before_ms=before['wall_ms'],after_ms=after['wall_ms'],speedup=before['wall_ms']/after['wall_ms'],
        before_kernel_ms=old_kernel,after_kernel_ms=new_kernel,uncached_candidates=8)

inventory={p.relative_to(ROOT).as_posix() for directory,pattern in
    [('app','*.py'),('app','detail_effects*'),('scripts','*.py'),('scripts','*.mjs'),('tests','*.py'),('docs','*.md')]
    for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'README.md','data/engine-effect-overrides.json'}
def previous(path):
    for root in (base,'research/ports/v53-typed-impacts-verified','research/ports/v52-resource-limits-verified'):
        p=ROOT/root/path
        if p.is_file():return p.read_bytes()
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports+baselines)
changed.update({'research/save-event-index-checkpoint.py','research/checkpoint_receipts.py','research/verify-event-index-batch.py',
    'research/verify-event-index-portable-counters.py','research/benchmark-normal-search.mjs','research/target-counters-api-fixture.json'})
checkpoint=dict(passed=True,generated_at=datetime.now(timezone.utc).isoformat(),objective_complete=False,
    abi=native['abi'],instruction_width=304,workspace_bytes_per_squad=workspace,workspace_added_bytes=workspace-1128952,
    archive_base=base,archive_kind='Delta over verified v54, resolving v53 and v52 for inherited files',
    checks=dict(accepted_compile_contexts=718,distinct_real_event_layouts=219,synthetic_boundary_layouts=2,
        shared_ordering_cases=25,native_counter_cases=18,portable_counter_quantity_controls=13,lightweight_methods=40,
        existing_batch_squads=8,normal_owned_api=True),reports=reports,historical_baselines=baselines,
    measurements=measurements,measurement_scope='One before/after uncached normal API batch for each fixture on RTX3070Ti; context warm; results equal. No universal speedup claim.',
    scope='Ordered immutable definition index, direct private continuations, existing shared instance lifecycle, and normal-path CUDA-event kernel profiling. No new character acceptance.',
    remaining='All-character goal remains active:22 standard compile-unaccepted characters and remaining effect/world families. Actor/component and special hit policies still require game evidence; no blanket game-correctness claim.')
print(json.dumps(save_checkpoint('research/event-index-checkpoint.json','research/ports/v55-event-index-verified',checkpoint,changed)))
