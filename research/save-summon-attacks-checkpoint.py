"""Close source attacks and once-per-timestamp worlds; outgoing routing pending."""
import hashlib,json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
base='research/ports/v72-summon-attacks-native-stage'
ancestors=[base]+['research/ports/'+n for n in ('v71-summon-sources-verified','v71-summon-sources-native-stage','v70-world-bindings-verified','v70-world-bindings-native-stage','v69-mode-inputs-verified','v69-mode-inputs-native-stage','v68-mode-commands-verified','v68-mode-commands-native-stage','v67-named-allies-verified','v67-target-scopes-verified','v67-target-scopes-native-stage','v66-attack-groups-foundation-verified','v65-attack-groups-native-stage','v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
reports=['research/summon-attacks-'+n+'.json' for n in ('native','ptx','unit','coverage','related-native','controls','batch-native','owned-api','after-api','cpu-init-after')]+['research/summon-attack-schedule-after.json','research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==13 for i in (0,1))
assert r[reports[2]]['tests_run']==89
assert r[reports[3]]['supported']==r[reports[3]]['existing_programs_identical']==187
assert len(r[reports[4]]['cases'])==5 and r[reports[5]]['tests_run']==7 and r[reports[6]]['batch_squads']==10
assert r[reports[7]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[7]]['mode_policy_roundtrip']['passed']
assert all(row['workspace_bytes']==1219088 for i in (0,1) for row in r[reports[i]]['cases'] if 'workspace_bytes' in row)
assert r[reports[9]]['frame0_calls'][1]['after']==[1] and r[reports[9]]['incoming_times']==[0,.016667]
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_summon_attacks_v72'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
before=read('research/summon-attack-schedule-before.json');after=r['research/summon-attack-schedule-after.json']
api_before=read('research/summon-attacks-before-api.json');api_after=r['research/summon-attacks-after-api.json']
assert before['passed'] and before['stimulus_sha256']==after['stimulus_sha256'] and before['semantic']==after['semantic']
assert before['repetitions']==after['repetitions']==5 and after['actual_incoming_hits']==2032
assert api_before['passed'] and api_before['candidates']==api_after['candidates']==8 and api_before['cache_hits']==api_after['cache_hits']==0
assert [{k:v for k,v in row.items() if k!='compute'} for row in api_before['results']]==[{k:v for k,v in row.items() if k!='compute'} for row in api_after['results']]
for receipt in (before,api_before):
    for name,digest in receipt['source_sha256'].items():
        candidates=[ROOT/name]+[ROOT/ancestor/name for ancestor in ancestors]
        assert any(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest for p in candidates),('before provenance',name)
old_audit=read('research/summon-attacks-cpu-init-before.json')
assert old_audit['defect_confirmed'] and old_audit['frame0_calls'][1]['after']==[2]
def previous(path):
    for ancestor in ancestors:
        p=ROOT/ancestor/path
        if p.is_file():return p.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={name for name in inventory if previous(name)!=(ROOT/name).read_bytes()}
changed.update(reports+['research/save-summon-attacks-checkpoint.py','research/checkpoint_receipts.py','research/verify-world-bindings-controls.py','research/verify-summon-attacks-coverage.py','research/verify-event-index-batch.py','research/summon-attack-schedule-before.json','research/benchmark-summon-attack-schedule.py','research/summon-attacks-before-api.json','research/summon-attacks-native-stage.json','research/world-bindings-api-fixture.json','research/benchmark-normal-search.mjs','research/attack-group-progress.json','research/summon-attacks-cpu-init-before.json'])
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=base,reports=reports,abi=native['abi'],instruction_width=344,character_width=169,workspace_bytes=1219088,state_growth_bytes=8,
    summon_attacks_connected=True,shared_per_pattern_schedules=True,cpu_and_gpu_world_frame_once_fixed=True,source_labels_retained=True,normal_summon_admission=False,attached_attack_debuffs_connected=False,autonomous_target_routing_connected=False,autonomous_multi_hit_connected=False,character_admission_changed=False,game_rules_verified=False,
    checks=dict(source_cases_per_backend=13,lightweight_methods=89,existing_body_part_cases=5,existing_world_incoming_methods=7,heterogeneous_squads=10,normal_owned_api=True,compile_only_supported=187,catalog=203,existing_programs_identical=187),
    efficiency=dict(approach='Skip actor scans when the next shared shot is not due or the schedule is complete; reuse existing incoming executor and queues',source_actors=127,world_frames=7201,actual_incoming_hits=2032,repetitions=5,source_before_ms=before['median_kernel_ms'],source_after_ms=after['median_kernel_ms'],source_kernel_speedup=after['comparison']['kernel_speedup'],normal_api8_before_ms=api_before['wall_ms'],normal_api8_after_ms=api_after['wall_ms'],normal_api_single_comparison=True,overall_speedup_claim=False),
    remaining='Dynamic enemy-count and per-target conditions, autonomous outgoing weapon/skill target routing, per-target state/effects, actual shot groups and explicit physical reach for positive raw multi_hit activation. Attack-attached debuffs and16 standard compile-unaccepted characters plus broader world/effect/favorite/equipment/model coverage remain. Whole-system efficiency follows all-character support.')
print(json.dumps(save_checkpoint('research/summon-attacks-checkpoint.json','research/ports/v72-summon-attacks-verified',c,changed)))
