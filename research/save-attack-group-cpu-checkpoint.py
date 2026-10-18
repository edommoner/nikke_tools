"""A verified CPU foundation and metadata optimization; GPU delivery is pending."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
from pathlib import Path
import sys
sys.path.insert(0,str(ROOT/'app'))
from lifecycle_specs import gpu_source_matches
reports=['research/attack-group-cpu-unit.json','research/attack-group-plan-after.json','research/attack-group-existing-api.json','research/runtime-wiring.json']
r=checked_receipts(reports);assert r[reports[0]]['tests_run']==65 and r[reports[2]]['pure_gpu_and_verified_and_cpu_equal']
assert r[reports[1]]['comparison']['speedup']>1 and gpu_source_matches()
base='research/ports/v63-attack-groups-cpu-stage'
ancestors=[base]+['research/ports/'+p for p in ('v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        p=ROOT/ancestor/path
        if p.is_file():return p.read_bytes()
unchanged=['app/'+name for name in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json','detail_effects.ptx','detail_effects-build.json')]
assert all(previous(p)==(ROOT/p).read_bytes() for p in unchanged)
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'README.md'}
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports+['research/save-attack-group-cpu-checkpoint.py','research/checkpoint_receipts.py','research/benchmark-attack-group-plans.py','research/attack-group-contract.json','research/attack-group-cpu-stage.json','research/attack-group-plan-before.json'])
c=dict(passed=True,cpu_stage_only=True,gpu_grouping_verified=False,autonomous_producer_connected=False,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=base,reports=reports,shared_unit_methods=65,
    unchanged_gpu={p:sha(p) for p in unchanged},character_admission_changed=False,standard_compile_supported=185,
    measurements=dict(cpu_metadata_before_ms=read('research/attack-group-plan-before.json')['median_ms'],cpu_metadata_after_ms=r[reports[1]]['median_ms'],cpu_metadata_speedup=r[reports[1]]['comparison']['speedup'],gpu_speedup_claim=False),
    remaining='Implement matching GPU group collection/seal delivery and real shot/world target routing before admitting multi_hit characters.18 standard compile-unaccepted characters and broader effect/world/model coverage remain; final whole-system efficiency review still required.')
print(json.dumps(save_checkpoint('research/attack-group-cpu-checkpoint.json','research/ports/v64-attack-groups-cpu-plans',c,changed)))
