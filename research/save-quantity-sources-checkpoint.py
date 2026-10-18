"""Finalize the faster verified variant; retain the rejected efficiency experiment."""
import json,hashlib
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=['research/quantity-sources-'+n+'.json' for n in ('native','ptx','unit','coverage','related-native','batch-native','owned-api','api-before','control-before')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
assert all(len(r['research/quantity-sources-'+b+'.json']['cases'])==10 for b in ('native','ptx'))
assert r[reports[2]]['tests_run']==58 and r[reports[3]]['supported']==184 and r[reports[3]]['existing_programs_identical']==183
assert len(r[reports[4]]['cases'])==25 and r[reports[5]]['batch_squads']==8 and r[reports[6]]['pure_gpu_and_verified_and_cpu_equal']
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_quantity_sources_v60'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
experiment=read('research/quantity-lookup-experiment.json');assert experiment['passed'] and not experiment['adopted']
for path,digest in experiment['source_sha256'].items():
    assert hashlib.sha256((ROOT/experiment['archive']/path).read_bytes()).hexdigest()==digest,path
base='research/ports/v60-quantity-sources-native-stage'
ancestors=[base]+['research/ports/'+p for p in ('v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        p=ROOT/ancestor/path
        if p.is_file():return p.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports+['research/save-quantity-sources-checkpoint.py','research/checkpoint_receipts.py','research/benchmark-normal-search.mjs','research/quantity-sources-api-fixture.json','research/staged-dot-api-fixture.json','research/quantity-sources-contract.json','research/verify-quantity-sources-coverage.py','research/quantity-sources-native-stage.json','research/quantity-lookup-experiment.json','research/quantity-lookup-api-after.json','research/quantity-lookup-control-after.json','research/resource-marker-dependency-audit.json'])
measurements={}
for label,old_name,new_name in [('quantity-api','quantity-sources-api-before','quantity-lookup-api-after'),('existing-control','quantity-sources-control-before','quantity-lookup-control-after')]:
    old=r['research/'+old_name+'.json'];new=read('research/'+new_name+'.json');measurements[label]=dict(accepted_variant_ms=old['wall_ms'],rejected_candidate_ms=new['wall_ms'],candidate_speedup=new['speedup'],scope='Single warm normal API eight-candidate comparison, no result cache. Small differences can be noise.')
checkpoint=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),abi=native['abi'],instruction_width=344,archive_base=base,reports=reports,measurements=measurements,efficiency_attempt=dict(adopted=False,archive=experiment['archive'],reason=experiment['reason']),
    checks=dict(independent_gpu_quantity_cases=6,cpu_query_scope_cases=1,raw_whole_squads=3,existing_ordering_cases=25,existing_batch_squads=8,lightweight_methods=58,normal_owned_api=True,compile_only_supported=184,catalog=203,existing_programs_identical=183),
    game_rules_verified=False,remaining='19 standard compile-unaccepted characters remain, plus equipment/favorite/world/effect/model review. Exact same-frame and collateral source-damage behavior remains unverified in game. Review overall efficiency again after all-character support.')
print(json.dumps(save_checkpoint('research/quantity-sources-checkpoint.json','research/ports/v60-quantity-sources-verified',checkpoint,changed)))
