"""New compiler admission using the existing, unchanged GPU target executor."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
reports=['research/named-allies-'+name+'.json' for name in ('native','ptx','unit','coverage','owned-api')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r[reports[i]]['cases'])==3 for i in (0,1))
assert all(r[reports[i]]['cases'][0]['batch_squads']==6 for i in (0,1))
assert all(len(r[reports[i]]['cases'][1]['named_effects_exercised'])==3 and not r[reports[i]]['cases'][2]['named_effects_exercised'] for i in (0,1))
assert r[reports[2]]['tests_run']==76 and r[reports[3]]['supported']==186 and r[reports[3]]['existing_programs_identical']==185
assert r[reports[4]]['pure_gpu_and_verified_and_cpu_equal']
base='research/ports/v67-target-scopes-verified'
ancestors=[base]+['research/ports/'+name for name in ('v67-target-scopes-native-stage','v66-attack-groups-foundation-verified','v65-attack-groups-native-stage','v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        source=ROOT/ancestor/path
        if source.is_file():return source.read_bytes()
unchanged=['app/'+name for name in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json','detail_effects.ptx','detail_effects-build.json')]
assert all(previous(name)==(ROOT/name).read_bytes() for name in unchanged)
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'README.md'}
changed={name for name in inventory if previous(name)!=(ROOT/name).read_bytes()}
changed.update(reports+['research/save-named-allies-checkpoint.py','research/checkpoint_receipts.py','research/verify-named-allies-coverage.py','research/named-allies-api-fixture.json','research/attack-group-progress.json'])
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=base,reports=reports,abi='detail_target_scopes_v67',
    checks=dict(independent_recipient_cases=6,quantity_times_per_recipient=4,raw_whole_squads=2,raw_named_effects_exercised=3,backends=['native','ptx'],lightweight_methods=76,normal_owned_api=True,compile_only_supported=186,catalog=203,existing_programs_identical=185),
    newly_admitted=r[reports[3]]['newly_admitted'],unchanged_gpu={name:sha(name) for name in unchanged},kernel_rebuilt=False,
    reuse=dict(checkpoint='research/target-scopes-checkpoint.json',reason='All185 previously accepted programs and all CUDA source/artifacts are byte-identical; existing broad ordering/arithmetic/batch verification is reused, not rerun or counted as new checks.'),
    efficiency=dict(approach='Exact catalog names, including punctuation, compile to existing ally target masks. No new execution branch, per-frame lookup, state allocation, shader build or JIT.',new_gpu_operation=False,gpu_speedup_claim=False),
    game_rules_verified=False,remaining='17 standard compile-unaccepted characters plus broader world/effect/equipment/favorite/model coverage. Autonomous shot groups, GPU actor world and per-target matched effect routing remain incomplete. Final overall efficiency review remains required after all-character support.')
print(json.dumps(save_checkpoint('research/named-allies-checkpoint.json','research/ports/v67-named-allies-verified',c,changed)))
