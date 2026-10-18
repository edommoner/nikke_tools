"""Freeze receiver mutations and retain the remaining lifecycle/routing scope."""
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
base='research/ports/v79-enemy-mutations-native-stage'
reports=['research/enemy-mutations-'+n+'.json' for n in ('native','ptx','unit','order-native','coverage','batch-native','owned-api','normal-after','fanout-native','fields-native')]+['research/gpu-mutations-after.json','research/runtime-wiring.json']
r=checked_receipts(reports)
for path in reports[:2]:assert r[path]['cases'][0]['observations']==22 and r[path]['cases'][0]['workspace_bytes']==1258016
assert r[reports[2]]['tests_run']==105 and len(r[reports[3]]['cases'])==25 and r[reports[4]]['existing_programs_identical']==187
assert r[reports[5]]['batch_squads']==10 and r[reports[6]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[6]]['mode_policy_roundtrip']['passed']
assert len(r[reports[8]]['cases'])==4 and len(r[reports[9]]['cases'])==3 and r[reports[9]]['controls']['rejected']==2
before=read('research/gpu-mutations-before.json');after=r[reports[10]];assert before['passed'] and before['semantic']==after['semantic']
raw_before=read('research/mutations-normal-before.json');raw_after=r[reports[7]]
for key in ('frames','positive_frames','first_positive','max_modifier','total_damage','members','burst_timeline'):assert raw_before[key]==raw_after[key],key
for receipt in (before,raw_before):
    for source,digest in receipt['source_sha256'].items():
        assert any((ROOT/a/source).is_file() and sha(a+'/'+source if a else source)==digest for a in ('',base)),('baseline provenance',source)
for manifest,binary,digest in [('app/detail_effects-sm86.json','app/detail_effects-sm86.cubin','binary_sha256'),('app/detail_effects-build.json','app/detail_effects.ptx','ptx_sha256')]:
    m=read(manifest);assert m['abi']=='detail_enemy_mutations_v79' and m['source_sha256']==sha('app/detail_effects.cu') and m[digest]==sha(binary)
files=reports+['research/gpu-mutations-before.json','research/mutations-normal-before.json','research/enemy-mutations-native-stage.json','research/benchmark-gpu-mutations.py','research/verify-enemy-fields-normal-witness.py','research/enemy-fields-api-fixture.json','research/verify-event-index-batch.py','research/save-enemy-mutations-checkpoint.py','research/checkpoint_receipts.py','README.md','docs/enemy-recipient-bindings.md','app/enemy_recipient_runtime.py','app/enemy_recipient_specs.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json','scripts/enemy_mutation_cases.py','scripts/verify-enemy-mutations-detail.py','scripts/verify-common-runtime-unit.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/enemy-mutations-checkpoint.json','research/ports/v79-enemy-mutations-verified',dict(passed=True,objective_complete=False,abi='detail_enemy_mutations_v79',workspace_bytes=1258016,state_growth_bytes=0,checks=dict(mutation_observations_per_backend=22,mutation_queries_per_backend=88,lightweight_methods=105,existing_ordering_cases=25,mixed_squads=10,existing_programs_identical=187,normal_owned_api=True),efficiency=dict(scope='Shared GPU receiver mutation workload including host preparation; not whole-squad damage',before_ms=before['median_ms'],after_ms=after['median_ms'],speedup=after['speedup']),normal_summon_admission=False,multi_hit_admission=False,remaining=['Recipient-bound initialization and periodic/bullet/finite-passive lifecycle','Delayed landing handles','Normal outgoing routing and physical shot producers','Remaining characters and broad equipment/effect coverage','Whole-system efficiency after full coverage']),files))
