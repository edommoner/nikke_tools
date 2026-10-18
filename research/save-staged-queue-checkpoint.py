"""Finalize the shared staged queue only after semantic and speed comparisons."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint

reports=['research/staged-queue-'+name+'.json' for name in ('native','ptx','unit','coverage','related-native','batch-native','owned-api','pool-after','api-after')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r['research/staged-queue-'+b+'.json']['cases'])==9 for b in ('native','ptx'))
assert r['research/staged-queue-unit.json']['tests_run']==55
assert len(r['research/staged-queue-related-native.json']['cases'])==25
assert r['research/staged-queue-batch-native.json']['batch_squads']==8
assert r['research/staged-queue-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_staged_queue_v59'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin')
assert portable['ptx_sha256']==sha('app/detail_effects.ptx')
base='research/ports/v58-staged-dot-native-stage'
ancestors=[base]+['research/ports/'+p for p in ('v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        p=ROOT/ancestor/path
        if p.is_file():return p.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports+['research/save-staged-queue-checkpoint.py','research/checkpoint_receipts.py','research/benchmark-staged-dot.py','research/benchmark-normal-search.mjs','research/staged-dot-api-fixture.json','research/staged-dot-native-stage.json','research/staged-dot-pool-before.json','research/staged-dot-api-before.json','research/damage-context-dependency-audit.json'])
pool=r['research/staged-queue-pool-after.json'];api=r['research/staged-queue-api-after.json'];coverage=r['research/staged-queue-coverage.json']
checkpoint=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),abi=native['abi'],instruction_width=344,archive_base=base,reports=reports,
    checks=dict(shared_primary_cases=9,existing_ordering_cases=25,existing_batch_squads=8,lightweight_methods=55,normal_owned_api=True,compile_only_supported=coverage['supported'],catalog=coverage['characters']),
    measurements=dict(pool64=dict(before_median_kernel_ms=read('research/staged-dot-pool-before.json')['median_kernel_ms'],after_median_kernel_ms=pool['median_kernel_ms'],speedup=pool['comparison']['kernel_speedup']),normal_api8=dict(before_ms=read('research/staged-dot-api-before.json')['wall_ms'],after_ms=api['wall_ms'],speedup=api['speedup'])),
    game_rules_verified=False,scope='Shared staged application and indexed deadline queue; native and portable final artifacts. Stress-pool measurements are distinct from normal gameplay latency.',
    remaining='20 standard compile-unaccepted characters remain, plus equipment/favorite/world/effect/model review. Review whole-system efficiency again after all-character support. Parent sequential-hit timing remains an explicitly warned approximation.')
print(json.dumps(save_checkpoint('research/staged-queue-checkpoint.json','research/ports/v59-staged-queue-verified',checkpoint,changed)))
