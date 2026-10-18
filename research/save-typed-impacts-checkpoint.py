"""Accept the typed landing boundary; archive only changes over verified v52."""
import json,re
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=[f'research/typed-impacts-{suffix}.json' for suffix in
    ('native','ptx','unit','related-native','owned-api','api-performance','dispatch-performance')]
receipts=checked_receipts(reports)
for backend in ('native','ptx'):
    report=receipts[f'research/typed-impacts-{backend}.json']
    assert report['source_stable'] and not report['cpu_trace_used_as_gpu_input'] and len(report['cases'])==3
    assert report['cases'][0]['packets']==72
    assert [(r['impact_frames'],r['impact_count']) for r in report['cases'][1:]]==[(482,1202),(482,2317)]
unit=receipts['research/typed-impacts-unit.json'];assert unit['tests_run']==29 and not unit['skipped']
related=receipts['research/typed-impacts-related-native.json'];assert related['batch_squads']==8 and len(related['cases'])==16 and not related['skipped']
assert receipts['research/typed-impacts-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
performance=receipts['research/typed-impacts-api-performance.json'];assert performance['candidates']==8 and performance['cache_hits']==0
dispatch=receipts['research/typed-impacts-dispatch-performance.json'];assert dispatch['pairs']==6 and dispatch['results_equal']
native,portable=read('app/detail_effects-sm86.json'),read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_typed_impacts_v53'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
workspace=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text())[1])
assert workspace==1108376
base='research/ports/v52-resource-limits-verified'
inventory={str(p.relative_to(ROOT)).replace('\\','/') for directory,pattern in
    [('app','*.py'),('app','detail_effects*'),('scripts','*.py'),('tests','*.py'),('docs','*.md')]
    for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory|={'README.md','data/engine-effect-overrides.json'}
changed={p for p in inventory if not (ROOT/base/p).is_file() or (ROOT/p).read_bytes()!=(ROOT/base/p).read_bytes()}
changed.update(reports)
changed.update({'research/save-typed-impacts-checkpoint.py','research/checkpoint_receipts.py','research/verify-typed-impact-related.py',
    'research/verify-typed-impact-unit.py','research/benchmark-lifecycle-dispatch.py','research/benchmark-normal-search.mjs',
    'research/base-copy-api-fixtures.json','research/damage-basis-additive-api-fixture.json'})
checkpoint=dict(passed=True,generated_at=datetime.now(timezone.utc).isoformat(),objective_complete=False,
    abi=native['abi'],instruction_width=295,workspace_bytes_per_squad=workspace,workspace_added_bytes=workspace-1103888,
    archive_base=base,archive_kind='Delta over verified v52; overlay these changed files onto the base snapshot',
    checks=dict(unique_primary_cases=3,native_primary_cases=3,portable_primary_cases=3,authored_transport_packets=72,
        independently_simulated_squads=2,frames_per_squad=482,lightweight_methods=29,existing_dependency_squads=8,
        existing_dependency_controls=16,normal_owned_api=True),reports=reports,
    measurements=dict(normal8_uncached_ms=performance['wall_ms'],normal8_baseline=performance['baseline'],
        normal8_speedup=performance['speedup'],cpu_dispatch_medians_ms=dispatch['medians_ms'],cpu_dispatch_speedup=dispatch['speedup']),
    scope='Common typed impact/state/event transport and precomputed CPU phase dispatch. No new character acceptance.',
    remaining='Target-associated counter lifecycle, death/threshold completion, supported impact-credit/refresh policies, enemy projectile/shield/add world routing and remaining effect families. Not all-character or in-game correctness.')
print(json.dumps(save_checkpoint('research/typed-impacts-checkpoint.json','research/ports/v53-typed-impacts-verified',checkpoint,changed)))
