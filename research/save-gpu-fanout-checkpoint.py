"""Close GPU receiver fanout without claiming outgoing summon combat admission."""
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
base='research/ports/v78-enemy-fanout-native-stage'
reports=['research/enemy-fanout-native.json','research/enemy-fanout-ptx.json']+['research/gpu-fanout-'+n+'.json' for n in ('unit','order-native','coverage','batch-native','owned-api','normal-after','after','after-api','fields-native')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
for path in reports[:2]:
    assert len(r[path]['cases'])==4 and all(c['workspace_bytes']==1258016 for c in r[path]['cases'])
    assert r[path]['cases'][2]['values']==[1,3,2] and r[path]['cases'][3]['logical_receivers']==96
assert r[reports[2]]['tests_run']==102 and len(r[reports[3]]['cases'])==25
assert r[reports[4]]['existing_programs_identical']==187 and r[reports[5]]['batch_squads']==10
assert r[reports[6]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[6]]['mode_policy_roundtrip']['passed']
assert len(r[reports[10]]['cases'])==3 and r[reports[10]]['controls']['rejected']==2
for manifest,binary,digest in [('app/detail_effects-sm86.json','app/detail_effects-sm86.cubin','binary_sha256'),('app/detail_effects-build.json','app/detail_effects.ptx','ptx_sha256')]:
    m=read(manifest);assert m['abi']=='detail_enemy_fanout_v78' and m['source_sha256']==sha('app/detail_effects.cu') and m[digest]==sha(binary)
before=read('research/gpu-fanout-before.json');after=r[reports[8]]
assert before['passed'] and before['semantic']==after['semantic']
raw_before=read('research/fanout-normal-before.json');raw_after=r[reports[7]]
for key in ('frames','positive_frames','first_positive','max_modifier','total_damage','members','burst_timeline'):assert raw_before[key]==raw_after[key],key
api_before=read('research/fanout-before-api.json');api_after=r[reports[9]]
assert api_before['passed'] and api_before['candidates']==api_after['candidates']==8 and api_before['cache_hits']==api_after['cache_hits']==0
assert [{k:v for k,v in row.items() if k!='compute'} for row in api_before['results']]==[{k:v for k,v in row.items() if k!='compute'} for row in api_after['results']]
for receipt in (before,raw_before,api_before):
    for source,digest in receipt['source_sha256'].items():
        assert any((ROOT/a/source).is_file() and sha(a+'/'+source if a else source)==digest for a in ('',base)),('baseline provenance',source)
files=reports+['research/gpu-fanout-before.json','research/fanout-normal-before.json','research/fanout-before-api.json','research/enemy-fanout-native-stage.json','research/benchmark-gpu-fanout.py','research/benchmark-normal-search.mjs','research/verify-enemy-fields-normal-witness.py','research/enemy-fields-api-fixture.json','research/verify-event-index-batch.py','research/save-gpu-fanout-checkpoint.py','research/checkpoint_receipts.py','README.md','docs/enemy-recipient-bindings.md','app/enemy_recipient_runtime.py','app/enemy_recipient_specs.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json','scripts/enemy_fanout_cases.py','scripts/verify-enemy-fanout-detail.py','scripts/verify-common-runtime-unit.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/gpu-fanout-checkpoint.json','research/ports/v78-enemy-fanout-verified',dict(passed=True,objective_complete=False,abi='detail_enemy_fanout_v78',workspace_bytes=1258016,functional_stage_workspace_bytes=1274400,snapshot_storage_saved_bytes=16384,checks=dict(fanout_cases_per_backend=4,logical_receivers_at_capacity=96,fixed_parts_at_capacity=32,lightweight_methods=102,existing_ordering_cases=25,mixed_squads=10,existing_programs_identical=187,normal_owned_api=True),efficiency=dict(scope='GPU shared updates; separate single normal API comparison',before_ms=before['median_ms'],after_ms=after['median_ms'],speedup=after['speedup'],api_before_ms=api_before['wall_ms'],api_after_ms=api_after['wall_ms'],api_speedup=api_after['speedup']),gpu_fanout_connected=True,normal_summon_admission=False,multi_hit_admission=False,remaining=['Recipient-aware removal and periodic/delayed lifecycle','Normal outgoing target routing and physical shot producers','Remaining characters and broad equipment/effect coverage','Whole-system efficiency after full coverage']),files))
