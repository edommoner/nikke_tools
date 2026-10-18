"""Freeze recipient fields and the static-world fast path with current evidence."""
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
base='research/ports/v76-enemy-fields-native-stage'
reports=['research/enemy-fields-'+n+'.json' for n in ('native','ptx','unit','order-native','coverage','batch-native','owned-api','normal-after','after-api')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
for path in reports[:2]:
    report=r[path]
    assert len(report['cases'])==3 and report['controls']['rejected']==2 and report['controls']['context_reused']
    assert all(c['independent_observations']==20 and c['workspace_bytes']==1225248 for c in report['cases'])
assert r[reports[2]]['tests_run']==100 and len(r[reports[3]]['cases'])==25
assert r[reports[4]]['supported']==r[reports[4]]['existing_programs_identical']==187
assert r[reports[5]]['batch_squads']==10 and r[reports[6]]['pure_gpu_and_verified_and_cpu_equal']
assert r[reports[6]]['mode_policy_roundtrip']['passed']
for manifest,binary,digest in [('app/detail_effects-sm86.json','app/detail_effects-sm86.cubin','binary_sha256'),('app/detail_effects-build.json','app/detail_effects.ptx','ptx_sha256')]:
    m=read(manifest);assert m['abi']=='detail_enemy_fields_v76' and m['source_sha256']==sha('app/detail_effects.cu') and m[digest]==sha(binary)
before=read('research/enemy-fields-before-api.json');after=r[reports[8]]
assert before['passed'] and before['candidates']==after['candidates']==8 and before['cache_hits']==after['cache_hits']==0
assert [{k:v for k,v in row.items() if k!='compute'} for row in before['results']]==[{k:v for k,v in row.items() if k!='compute'} for row in after['results']]
raw_before=read('research/enemy-fields-normal-before.json');raw_after=r[reports[7]]
for key in ('frames','positive_frames','first_positive','max_modifier','total_damage','members','burst_timeline'):assert raw_before[key]==raw_after[key],key
for receipt in (before,raw_before):
    for source,digest in receipt['source_sha256'].items():
        assert any((ROOT/a/source).is_file() and sha(a+'/'+source if a else source)==digest for a in ('',base)),('baseline provenance',source)
files=reports+['research/enemy-fields-before-api.json','research/enemy-fields-normal-before.json','research/enemy-fields-native-stage.json','research/enemy-fields-api-fixture.json','research/verify-enemy-fields-normal-witness.py','research/benchmark-normal-search.mjs','research/verify-event-index-batch.py','research/checkpoint_receipts.py','research/save-enemy-fields-checkpoint.py','README.md','docs/enemy-recipient-bindings.md',
'app/enemy_recipient_specs.py','app/enemy_recipient_runtime.py','app/target_context_runtime.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json','scripts/build-detail-native.py','scripts/build-detail-ptx.py','scripts/enemy_recipient_cases.py','scripts/verify-enemy-fields-detail.py','scripts/verify-common-runtime-unit.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/enemy-fields-checkpoint.json','research/ports/v76-enemy-fields-verified',dict(passed=True,objective_complete=False,abi='detail_enemy_fields_v76',workspace_bytes=1225248,state_growth_bytes=6144,checks=dict(families_per_backend=3,observations_per_family=20,negative_controls_per_backend=2,lightweight_methods=100,existing_ordering_cases=25,mixed_squads=10,existing_programs_identical=187,normal_owned_api=True),efficiency=dict(scope='Body-only configured worlds omit recipient tracking; single normal API comparison',before_ms=before['wall_ms'],after_ms=after['wall_ms'],speedup=before['wall_ms']/after['wall_ms'],raw_positive_frames=raw_after['positive_frames']),normal_summon_admission=False,multi_hit_admission=False,remaining=['Independent overlapping recipient fanout and refresh','Recipient-aware removal and periodic/delayed lifecycle','Normal outgoing target routing and physical shot producers','Remaining standard characters and broader equipment/effect coverage','Whole-system efficiency after full coverage']),files))
