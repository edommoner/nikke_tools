"""Close dynamic count predicates, retaining explicitly scoped prior evidence."""
import hashlib,json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
stage='research/ports/v73-world-conditions-native-stage'
ancestors=[stage]+['research/ports/'+n for n in ('v72-summon-attacks-verified','v72-summon-attacks-native-stage','v71-summon-sources-verified','v71-summon-sources-native-stage','v70-world-bindings-verified','v70-world-bindings-native-stage','v69-mode-inputs-verified','v69-mode-inputs-native-stage','v68-mode-commands-verified','v68-mode-commands-native-stage','v67-named-allies-verified','v67-target-scopes-verified','v67-target-scopes-native-stage','v66-attack-groups-foundation-verified','v65-attack-groups-native-stage','v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
reports=['research/world-conditions-'+n+'.json' for n in ('native','ptx','source-native','source-ptx','unit','coverage','batch-native','owned-api','after-api')]+['research/world-conditions-specialization-benchmark.json','research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==2 for i in (0,1))
assert all(len(r[reports[i]]['cases'])==13 for i in (2,3))
assert r[reports[4]]['tests_run']==92 and r[reports[5]]['supported']==r[reports[5]]['existing_programs_identical']==187
assert r[reports[6]]['batch_squads']==10 and r[reports[7]]['pure_gpu_and_verified_and_cpu_equal']
assert r[reports[7]]['original_total']!=r[reports[7]]['total'],'Temporary growth change must actually affect this squad'
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_world_conditions_v73'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
for i in (0,1,2,3):
    assert all(row['workspace_bytes']==1219088 for row in r[reports[i]]['cases'] if 'workspace_bytes' in row)
before=read('research/world-conditions-before-api.json');after=r[reports[8]]
benchmark=r[reports[9]]
assert benchmark['repetitions']==3 and benchmark['candidates']==8 and benchmark['folded_conditions']==16
assert before['passed'] and before['candidates']==after['candidates']==8 and before['cache_hits']==after['cache_hits']==0
assert [{k:v for k,v in row.items() if k!='compute'} for row in before['results']]==[{k:v for k,v in row.items() if k!='compute'} for row in after['results']]
for name,digest in before['source_sha256'].items():
    assert any(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest for p in [ROOT/name]+[ROOT/base/name for base in ancestors]),('baseline provenance',name)
# Broad prior world/receiver matrices can be reused only while all their CUDA
# implementations remain byte-identical. Prove the full diff is this predicate
# helper, its two runtime gates and the exported ABI, rather than assuming it.
cu=(ROOT/'app/detail_effects.cu').read_text(encoding='utf-8')
old=(ROOT/'research/ports/v72-summon-attacks-verified/app/detail_effects.cu').read_text(encoding='utf-8')
from sys import path
path.insert(0,str(ROOT/'app'))
from world_condition_specs import BEGIN,END,render_cuda
normalized=cu.replace(BEGIN+render_cuda()+END,'').replace('detail_world_conditions_v73','detail_summon_attacks_v72')
normalized=normalized.replace('  // Finite effects latch activation; persistent predicates read current state.','  // Only persistent self-state/full-burst predicates are reevaluated at query time.')
normalized=normalized.replace('&&type!=WORLD_COUNT_ABOVE&&type!=WORLD_COUNT_BELOW','')
normalized=normalized.replace('  if((type==WORLD_COUNT_ABOVE||type==WORLD_COUNT_BELOW)&&!world_count_condition(type,s->add_live_snapshot,arg))return 0;\n','')
assert normalized==old,'Review changed world/receiver code before reusing prior evidence'
prior=read('research/summon-attacks-checkpoint.json')
assert prior['passed'] and prior['checks']['existing_body_part_cases']==5 and prior['checks']['existing_world_incoming_methods']==7

def previous(name):
    for base in ancestors:
        p=ROOT/base/name
        if p.is_file():return p.read_bytes()

inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={name for name in inventory if previous(name)!=(ROOT/name).read_bytes()}
changed.update(reports+['research/save-world-conditions-checkpoint.py','research/checkpoint_receipts.py','research/attack-group-progress.json','research/world-conditions-native-stage.json','research/world-conditions-before-api.json','research/world-conditions-api-fixture.json','research/world-conditions-owned-api-fixture.json','research/benchmark-world-count-specialization.py','research/benchmark-normal-search.mjs','research/verify-event-index-batch.py'])
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=stage,abi=native['abi'],workspace_bytes=1219088,state_growth_bytes=0,
    dynamic_count_predicates_verified=True,frame_snapshot_reused=True,inclusive_thresholds=True,finite_and_persistent_lifetimes_shared=True,static_world_specialization=True,
    normal_summon_admission=False,target_kind_context_connected=False,autonomous_target_routing_connected=False,autonomous_multi_hit_connected=False,character_admission_changed=False,game_rules_verified=False,
    checks=dict(predicate_cases_per_backend=2,predicate_observations_per_case=16,existing_source_cases_per_backend=13,lightweight_methods=92,heterogeneous_squads=10,normal_owned_api=True,compile_only_supported=187,catalog=203,existing_programs_identical=187),
    reused_evidence=dict(checkpoint='research/summon-attacks-checkpoint.json',body_part_cases=5,world_incoming_methods=7,reason='Full CUDA source unchanged outside new predicate helper/runtime gates/export; old standard programs and weapon inputs identical'),
    efficiency=dict(approach='Fold count predicates only when validated world has no add source; delayed sources retain dynamic conditions',normal_api8_before_ms=before['wall_ms'],normal_api8_after_ms=after['wall_ms'],normal_api_single_comparison=True,interleaved_kernel_medians=benchmark['median_kernel_ms'],interleaved_kernel_ratio=benchmark['kernel_ratio'],kernel_repetitions=3,overall_speedup_claim=False),
    remaining='Per-target contexts/conditions/state/effects, autonomous outgoing routing, real attack boundaries and explicit physical reach with positive raw multi_hit activation;16 standard compile-unaccepted characters and broader world/effect/favorite/equipment/model coverage. Whole-system efficiency follows all-character support.')
print(json.dumps(save_checkpoint('research/world-conditions-checkpoint.json','research/ports/v73-world-conditions-verified',c,changed)))
