"""Finalize retained storage without claiming autonomous actor/effect routing."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=['research/target-scopes-'+name+'.json' for name in ('native','ptx','unit','coverage','related-native','batch-native','owned-api','control-api','metadata-cost')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==10 for i in (0,1))
assert r[reports[2]]['tests_run']==74 and r[reports[3]]['supported']==r[reports[3]]['existing_programs_identical']==185
assert len(r[reports[4]]['cases'])==25 and r[reports[5]]['batch_squads']==8 and r[reports[6]]['pure_gpu_and_verified_and_cpu_equal']
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_target_scopes_v67'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
assert all(case.get('workspace_bytes',1216840)==1216840 for case in r[reports[0]]['cases'])
base='research/ports/v67-target-scopes-native-stage'
ancestors=[base]+['research/ports/'+name for name in ('v66-attack-groups-foundation-verified','v65-attack-groups-native-stage','v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        source=ROOT/ancestor/path
        if source.is_file():return source.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={name for name in inventory if previous(name)!=(ROOT/name).read_bytes()}
changed.update(reports+['research/save-target-scopes-checkpoint.py','research/checkpoint_receipts.py','research/target-scopes-native-stage.json','research/attack-group-contract.json','research/attack-group-progress.json',
    'research/benchmark-gpu-attack-plans.py','research/benchmark-normal-search.mjs','research/resource-marker-api-fixture.json','research/staged-dot-api-fixture.json','research/verify-attack-groups-coverage.py'])
cost=r[reports[8]];normal=r[reports[7]]
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=base,reports=reports,abi=native['abi'],instruction_width=344,workspace_bytes=1216840,
    retained_target_storage_verified=True,cpu_add_landing_bridge_verified=True,autonomous_producer_connected=False,matched_target_effect_routing_connected=False,character_admission_changed=False,game_rules_verified=False,
    checks=dict(gpu_cases_per_backend=10,lightweight_methods=74,existing_ordering_cases=25,heterogeneous_squads=8,normal_owned_api=True,compile_only_supported=185,catalog=203,existing_programs_identical=185),
    efficiency=dict(approach='Reuse existing arrays and slot states; no target-list copy or per-squad memory growth',metadata_median_ms=cost['median_kernel_ms'],metadata_speedup=cost['comparison']['kernel_speedup'],normal_api8_ms=normal['wall_ms'],normal_single_comparison_speedup=normal['speedup'],overall_speedup_claim=False),
    remaining='Actual shot boundaries, GPU actor world and per-actor child effect application remain pending.18 standard compile-unaccepted characters and broader world/effect/equipment/favorite/model validation remain. Final whole-system efficiency review is required after all-character support.')
print(json.dumps(save_checkpoint('research/target-scopes-checkpoint.json','research/ports/v67-target-scopes-verified',c,changed)))
