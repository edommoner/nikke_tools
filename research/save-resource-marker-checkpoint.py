"""Compiler admission over an unchanged, already-verified GPU interpreter."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
reports=['research/resource-marker-'+n+'.json' for n in ('native','ptx','unit','coverage','owned-api')]
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==3 for i in (0,1))
assert r[reports[2]]['tests_run']==59 and r[reports[3]]['supported']==185 and r[reports[3]]['existing_programs_identical']==184
assert r[reports[4]]['pure_gpu_and_verified_and_cpu_equal']
base='research/ports/v60-quantity-sources-verified'
ancestors=[base]+['research/ports/'+p for p in ('v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        p=ROOT/ancestor/path
        if p.is_file():return p.read_bytes()
unchanged=['app/'+name for name in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json','detail_effects.ptx','detail_effects-build.json')]
assert all(previous(p)==(ROOT/p).read_bytes() for p in unchanged)
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'README.md'}
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports+['research/save-resource-marker-checkpoint.py','research/checkpoint_receipts.py','research/verify-resource-marker-coverage.py','research/resource-marker-api-fixture.json','research/resource-marker-dependency-audit.json'])
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),abi='detail_quantity_sources_v60',archive_base=base,reports=reports,
    checks=dict(independent_lifecycle_frames=15,raw_whole_squads=2,backends=['native','ptx'],lightweight_methods=59,normal_owned_api=True,compile_only_supported=185,catalog=203,existing_programs_identical=184),
    unchanged_gpu={p:sha(p) for p in unchanged},kernel_rebuilt=False,
    reuse=dict(previous_checkpoint='research/quantity-sources-checkpoint.json',reason='All184 previously accepted programs identical and all CUDA source/artifact bytes unchanged. Existing broad arithmetic/order/batch runtime proofs reused, not rerun or counted as new checks.'),
    efficiency=dict(approach='Reuse existing state carriers and explicit charge conditions; no new GPU arithmetic or state executor, no ABI/width/workspace growth and no kernel build/JIT required.',gpu_speedup_claim=False),
    game_rules_verified=False,remaining='18 standard compile-unaccepted characters plus favorite/equipment/world/effect/model checks remain. Review overall efficiency after all-character support.')
print(json.dumps(save_checkpoint('research/resource-marker-checkpoint.json','research/ports/v62-resource-marker-verified',c,changed)))
