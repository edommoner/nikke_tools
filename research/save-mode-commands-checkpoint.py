"""Close the common mode commands, leaving autonomous manual input explicit."""
import hashlib,json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=['research/mode-commands-'+name+'.json' for name in ('native','ptx','unit','coverage','mode-controls','related-native','batch-native','owned-api','control-api')]+['research/ammo-notice-queue-after.json','research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==4 for i in (0,1))
assert r[reports[2]]['tests_run']==80 and r[reports[3]]['supported']==r[reports[3]]['existing_programs_identical']==186
assert len(r[reports[4]]['cases'])==2 and len(r[reports[5]]['cases'])==25 and r[reports[6]]['batch_squads']==8
assert r[reports[7]]['pure_gpu_and_verified_and_cpu_equal']
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_mode_commands_v68'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
base='research/ports/v68-mode-commands-native-stage'
before=read('research/ammo-notice-queue-before.json');after=r['research/ammo-notice-queue-after.json']
assert before['passed'] and before['stimulus_sha256']==after['stimulus_sha256'] and before['semantic']==after['semantic'] and after['comparison']['kernel_speedup']>1
for name,digest in before['source_sha256'].items():
    origin=ROOT/base/name if name in ('app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json') else ROOT/name
    assert hashlib.sha256(origin.read_bytes()).hexdigest()==digest,('before provenance',name)
ancestors=[base]+['research/ports/'+name for name in ('v67-named-allies-verified','v67-target-scopes-verified','v67-target-scopes-native-stage','v66-attack-groups-foundation-verified','v65-attack-groups-native-stage','v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        source=ROOT/ancestor/path
        if source.is_file():return source.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={name for name in inventory if previous(name)!=(ROOT/name).read_bytes()}
changed.update(reports+['research/save-mode-commands-checkpoint.py','research/checkpoint_receipts.py','research/verify-mode-command-controls.py','research/verify-mode-commands-coverage.py','research/benchmark-ammo-notice-queue.py','research/ammo-notice-queue-before.json','research/mode-commands-native-stage.json','research/attack-group-progress.json','research/named-allies-api-fixture.json','research/staged-dot-api-fixture.json','research/benchmark-normal-search.mjs'])
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=base,reports=reports,abi=native['abi'],instruction_width=344,workspace_bytes=1216840,
    common_toggle_and_equivalent_ammo_verified=True,autonomous_manual_reload_input_connected=False,character_admission_changed=False,game_rules_verified=False,
    checks=dict(command_cases_per_backend=4,lightweight_methods=80,existing_mode_integrations=2,existing_ordering_cases=25,heterogeneous_squads=8,normal_owned_api=True,compile_only_supported=186,catalog=203,existing_programs_identical=186),
    efficiency=dict(approach='Reuse existing mode-end and per-frame notice queues; skip only when the immutable event index contains no matching listener',metadata_before_ms=before['median_kernel_ms'],metadata_after_ms=after['median_kernel_ms'],metadata_speedup=after['comparison']['kernel_speedup'],normal_api8_ms=r['research/mode-commands-control-api.json']['wall_ms'],overall_speedup_claim=False),
    remaining='Connect autonomous manual-reload mode input and require actual raw skill mode shots/notices before admitting Crystal Wave Cinderella.17 standard compile-unaccepted characters and broader world/effect/favorite/equipment/model coverage remain. Final overall efficiency review is required after all-character support.')
print(json.dumps(save_checkpoint('research/mode-commands-checkpoint.json','research/ports/v68-mode-commands-verified',c,changed)))
