"""Verified GPU collector/condition delivery, with autonomous routing still pending."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=['research/attack-groups-'+n+'.json' for n in ('native','ptx','unit','coverage','related-native','batch-native','owned-api','control-api')]+['research/gpu-attack-plan-after.json','research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==7 for i in (0,1))
assert r[reports[2]]['tests_run']==66 and r[reports[3]]['supported']==185 and r[reports[3]]['existing_programs_identical']==185
assert len(r[reports[4]]['cases'])==25 and r[reports[5]]['batch_squads']==8 and r[reports[6]]['pure_gpu_and_verified_and_cpu_equal']
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_attack_plans_v66'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
base='research/ports/v65-attack-groups-native-stage'
ancestors=[base]+['research/ports/'+p for p in ('v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        p=ROOT/ancestor/path
        if p.is_file():return p.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports+['research/save-attack-groups-gpu-checkpoint.py','research/checkpoint_receipts.py','research/benchmark-gpu-attack-plans.py','research/benchmark-normal-search.mjs','research/gpu-attack-plan-before.json','research/attack-groups-native-stage.json','research/attack-group-contract.json','research/attack-world-producer-audit.json','research/verify-attack-groups-coverage.py','research/resource-marker-api-fixture.json','research/staged-dot-api-fixture.json','research/quantity-sources-control-before.json'])
before=read('research/gpu-attack-plan-before.json');after=r['research/gpu-attack-plan-after.json']
c=dict(passed=True,objective_complete=False,gpu_collection_and_condition_notifications_verified=True,autonomous_producer_connected=False,matched_target_effect_routing_connected=False,character_admission_changed=False,
    generated_at=datetime.now(timezone.utc).isoformat(),abi=native['abi'],instruction_width=344,workspace_bytes=1216840,archive_base=base,reports=reports,
    checks=dict(shared_gpu_cases=7,existing_ordering_cases=25,existing_batch_squads=8,lightweight_methods=66,normal_owned_api=True,compile_only_supported=185,catalog=203,existing_programs_identical=185),
    measurements=dict(metadata_stress_before_ms=before['median_kernel_ms'],metadata_stress_after_ms=after['median_kernel_ms'],metadata_stress_speedup=after['comparison']['kernel_speedup'],normal_api8_ms=r['research/attack-groups-control-api.json']['wall_ms'],normal_api_comparison_speedup=r['research/attack-groups-control-api.json']['speedup'],scope='Metadata stress3 warm samples; ordinary API one comparison. Not an overall gameplay speedup.'),
    game_rules_verified=False,remaining='Connect actual weapon shot boundaries, stable world actor identities, per-target routing and retained immutable matched-target scope before allowing normal multi_hit character admission.18 standard compile-unaccepted characters and broader world/effect/equipment/favorite/model coverage remain. Final overall efficiency review remains required after all-character support.')
print(json.dumps(save_checkpoint('research/attack-groups-gpu-checkpoint.json','research/ports/v66-attack-groups-foundation-verified',c,changed)))
