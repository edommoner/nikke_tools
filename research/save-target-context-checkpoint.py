"""Close target predicate scopes; actor-specific effect storage remains pending."""
import hashlib,json,re
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
base='research/ports/v74-target-context-native-stage'
ancestors=[base]+['research/ports/'+n for n in ('v73-world-conditions-verified','v73-world-conditions-native-stage','v72-summon-attacks-verified','v72-summon-attacks-native-stage','v71-summon-sources-verified','v71-summon-sources-native-stage','v70-world-bindings-verified','v70-world-bindings-native-stage','v69-mode-inputs-verified','v69-mode-inputs-native-stage','v68-mode-commands-verified','v68-mode-commands-native-stage','v67-named-allies-verified','v67-target-scopes-verified','v67-target-scopes-native-stage','v66-attack-groups-foundation-verified','v65-attack-groups-native-stage','v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
reports=['research/target-context-'+n+'.json' for n in ('native','ptx','unit','order-native','coverage','batch-native','owned-api','after-api','world-count-native')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==2 for i in (0,1))
assert all(row['workspace_bytes']==1219104 for i in (0,1) for row in r[reports[i]]['cases'])
assert r[reports[2]]['tests_run']==95 and len(r[reports[3]]['cases'])==25
assert r[reports[4]]['supported']==r[reports[4]]['existing_programs_identical']==187
assert r[reports[5]]['batch_squads']==10 and r[reports[6]]['pure_gpu_and_verified_and_cpu_equal']
assert r[reports[6]]['original_total']!=r[reports[6]]['total'] and r[reports[6]]['mode_policy_roundtrip']['passed']
assert len(r[reports[8]]['cases'])==2
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_target_context_v74'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
before=read('research/target-context-before-api.json');after=r[reports[7]]
assert before['passed'] and before['candidates']==after['candidates']==8 and before['cache_hits']==after['cache_hits']==0
assert [{k:v for k,v in row.items() if k!='compute'} for row in before['results']]==[{k:v for k,v in row.items() if k!='compute'} for row in after['results']]
for name,digest in before['source_sha256'].items():
    assert any(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest for p in [ROOT/name]+[ROOT/a/name for a in ancestors]),('baseline provenance',name)

def function(source,name):
    match=re.search(r'^__device__[^\n]*\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',source,re.M)
    assert match,name
    at=match.end();depth=1
    while depth:
        depth+=(source[at]=='{')-(source[at]=='}');at+=1
    return source[match.start():at]

cu=(ROOT/'app/detail_effects.cu').read_text(encoding='utf-8')
prior_cu=(ROOT/'research/ports/v72-summon-attacks-verified/app/detail_effects.cu').read_text(encoding='utf-8')
unchanged=('world_actor_index','world_actor','boss_frame','boss_init','gather_incoming','incoming_targets','incoming_land','add_land','parts_land')
for name in unchanged:assert function(cu,name)==function(prior_cu,name),('Review world/receiver reuse',name)
prior=read('research/summon-attacks-checkpoint.json')
assert prior['passed'] and prior['checks']['source_cases_per_backend']==13 and prior['checks']['existing_world_incoming_methods']==7

def previous(path):
    for a in ancestors:
        p=ROOT/a/path
        if p.is_file():return p.read_bytes()

inventory={p.relative_to(ROOT).as_posix() for d,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/d).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={name for name in inventory if previous(name)!=(ROOT/name).read_bytes()}
changed.update(reports+['research/save-target-context-checkpoint.py','research/checkpoint_receipts.py','research/attack-group-progress.json','research/target-context-native-stage.json','research/target-context-before-api.json','research/world-bindings-api-fixture.json','research/benchmark-normal-search.mjs','research/verify-event-index-batch.py'])
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=base,abi=native['abi'],workspace_bytes=1219104,state_growth_bytes=16,
    target_kind_context_connected=True,counter_completion_target_connected=True,completion_without_impact_connected=True,nested_target_restore_verified=True,HP_reentry_combination_verified=True,immutable_interest_skip_verified=True,
    normal_summon_admission=False,autonomous_aim_connected=False,per_actor_effect_state_connected=False,autonomous_target_routing_connected=False,autonomous_multi_hit_connected=False,character_admission_changed=False,game_rules_verified=False,
    checks=dict(target_cases_per_backend=2,target_observations_per_case=10,lightweight_methods=95,existing_ordering_cases=25,world_count_cases=2,heterogeneous_squads=10,normal_owned_api=True,compile_only_supported=187,catalog=203,existing_programs_identical=187),
    reused_evidence=dict(checkpoint='research/summon-attacks-checkpoint.json',source_cases_per_backend=13,world_incoming_methods=7,reason='Named source/receiver/world functions byte-identical; new context exercises real add pools and current generation directly',identical_functions=list(unchanged)),
    efficiency=dict(approach='Compute immutable interest once; skip context stack updates/restoration when no dynamic target predicate can observe them',normal_api8_before_ms=before['wall_ms'],normal_api8_after_ms=after['wall_ms'],normal_api_single_comparison=True,overall_speedup_claim=False),
    remaining='Per-actor effect state, delayed target handles, autonomous aim/outgoing routing, real attack groups and explicit physical reach for positive raw multi_hit activation;16 standard compile-unaccepted characters and broader world/effect/favorite/equipment/model coverage. Whole-system efficiency follows all-character support.')
print(json.dumps(save_checkpoint('research/target-context-checkpoint.json','research/ports/v74-target-context-verified',c,changed)))
