"""Close shared world bindings, preserving unsupported live-world producers."""
import hashlib,json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
reports=['research/world-bindings-'+n+'.json' for n in ('native','ptx','unit','coverage','controls','batch-native','owned-api','after-api')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==5 for i in (0,1))
assert r[reports[2]]['tests_run']==85
assert r[reports[3]]['supported']==r[reports[3]]['existing_programs_identical']==187
assert r[reports[3]]['old_world_prefix_identical'] and r[reports[3]]['weapon_rows_identical']
assert r[reports[4]]['tests_run']==7 and r[reports[5]]['batch_squads']==10
assert r[reports[6]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[6]]['mode_policy_roundtrip']['passed']
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_world_bindings_v70'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
base='research/ports/v70-world-bindings-native-stage'
before=read('research/world-bindings-before-api.json');after=r[reports[7]]
assert before['passed'] and before['candidates']==after['candidates']==8 and before['cache_hits']==after['cache_hits']==0
assert [{k:v for k,v in row.items() if k!='compute'} for row in before['results']]==[{k:v for k,v in row.items() if k!='compute'} for row in after['results']]
for name,digest in before['source_sha256'].items():
    origin=ROOT/base/name if name in ('app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json') else ROOT/name
    assert hashlib.sha256(origin.read_bytes()).hexdigest()==digest,('before provenance',name)
ancestors=[base]+['research/ports/'+n for n in ('v69-mode-inputs-verified','v69-mode-inputs-native-stage','v68-mode-commands-verified','v68-mode-commands-native-stage','v67-named-allies-verified','v67-target-scopes-verified','v67-target-scopes-native-stage','v66-attack-groups-foundation-verified','v65-attack-groups-native-stage','v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        p=ROOT/ancestor/path
        if p.is_file():return p.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={name for name in inventory if previous(name)!=(ROOT/name).read_bytes()}
changed.update(reports+['research/save-world-bindings-checkpoint.py','research/checkpoint_receipts.py','research/verify-world-bindings-controls.py','research/verify-world-bindings-coverage.py','research/verify-event-index-batch.py','research/world-bindings-before-api.json','research/world-bindings-native-stage.json','research/world-bindings-api-fixture.json','research/benchmark-normal-search.mjs','research/attack-group-progress.json'])
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=base,reports=reports,abi=native['abi'],instruction_width=344,character_width=169,workspace_bytes=1216840,world_input_extra_bytes=8200,
    configured_world_bindings_shared=True,body_and_fixed_part_landings_connected=True,summon_live_pool_connected=False,autonomous_multi_hit_connected=False,character_admission_changed=False,game_rules_verified=False,
    checks=dict(world_cases_per_backend=5,lightweight_methods=85,existing_world_and_incoming_methods=7,heterogeneous_squads=10,normal_owned_api=True,compile_only_supported=187,catalog=203,existing_programs_identical=187,old_world_prefix_identical=True),
    efficiency=dict(approach='Canonical immutable actor table and direct body/part lookup; reuse live source arrays without copying state',normal_api8_before_ms=before['wall_ms'],normal_api8_after_ms=after['wall_ms'],single_comparison_speedup=before['wall_ms']/after['wall_ms'],repeated_median=False,overall_speedup_claim=False),
    remaining='Connect GPU summon source state, real weapon attack boundaries and per-target child routing. Require nonzero raw multi_hit activation.16 standard compile-unaccepted characters and broader world/effect/favorite/equipment/model coverage remain; final whole-system efficiency follows all-character support.')
print(json.dumps(save_checkpoint('research/world-bindings-checkpoint.json','research/ports/v70-world-bindings-verified',c,changed)))
