"""Freeze periodic target sampling and ordered registration snapshots."""
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
base='research/ports/v80-periodic-targets-native-stage'
reports=['research/periodic-targets-'+n+'.json' for n in ('native','ptx','unit','order-native','coverage','batch-native','owned-api','normal-after','mutations-native','after','normal-performance')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
for path in reports[:2]:
    report=r[path];assert len(report['cases'])==6 and all(c['workspace_bytes']==1260136 for c in report['cases'])
    assert [c['observations'] for c in report['cases']]==[23,8,8,14,9,8]
    assert report['controls']['rejected']==2 and report['controls']['context_reused']
assert r[reports[2]]['tests_run']==109 and len(r[reports[3]]['cases'])==25 and r[reports[4]]['existing_programs_identical']==187
assert r[reports[5]]['batch_squads']==10 and r[reports[6]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[6]]['mode_policy_roundtrip']['passed']
assert r[reports[8]]['cases'][0]['observations']==22
before=read('research/periodic-targets-before.json');after=r[reports[9]];assert before['passed'] and before['stimulus_sha256']==after['stimulus_sha256'] and before['semantic']==after['semantic']
assert after['interleaved'] and len(after['samples'])==len(after['old_samples'])==5
normal=r[reports[10]];assert normal['interleaved'] and normal['batch_squads']==8 and normal['normal_full_calculation']
raw_before=read('research/periodic-targets-normal-before.json');raw_after=r[reports[7]]
for key in ('frames','positive_frames','first_positive','max_modifier','total_damage','members','burst_timeline'):assert raw_before[key]==raw_after[key],key
for receipt in (before,raw_before):
    for source,digest in receipt['source_sha256'].items():
        assert any((ROOT/a/source).is_file() and sha(a+'/'+source if a else source)==digest for a in ('',base)),('baseline provenance',source)
for manifest,binary,digest in [('app/detail_effects-sm86.json','app/detail_effects-sm86.cubin','binary_sha256'),('app/detail_effects-build.json','app/detail_effects.ptx','ptx_sha256')]:
    m=read(manifest);assert m['abi']=='detail_periodic_targets_v80' and m['source_sha256']==sha('app/detail_effects.cu') and m[digest]==sha(binary)
files=reports+['research/periodic-targets-before.json','research/periodic-targets-normal-before.json','research/periodic-targets-native-stage.json','research/benchmark-periodic-targets.py','research/benchmark-periodic-normal.py','research/verify-enemy-fields-normal-witness.py','research/enemy-fields-api-fixture.json','research/verify-event-index-batch.py','research/save-periodic-targets-checkpoint.py','research/checkpoint_receipts.py','README.md','docs/enemy-recipient-bindings.md','app/periodic_target_runtime.py','app/periodic_target_specs.py','app/world_actor_runtime.py','app/impact_runtime.py','app/effect_spec.py','app/enemy_recipient_specs.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json','scripts/periodic_target_cases.py','scripts/verify-periodic-targets-detail.py','scripts/verify-common-runtime-unit.py','tests/test_periodic_target_runtime.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/periodic-targets-checkpoint.json','research/ports/v80-periodic-targets-verified',dict(passed=True,objective_complete=False,abi='detail_periodic_targets_v80',workspace_bytes=1260136,functional_stage_workspace_bytes=1259104,index_growth_bytes=1032,checks=dict(shared_cases_per_backend=6,negative_controls_per_backend=2,lightweight_methods=109,existing_ordering_cases=25,mixed_squads=10,existing_programs_identical=187,normal_owned_api=True),efficiency=dict(timer_workload_before_kernel_ms=after['before_kernel_ms'],timer_workload_after_kernel_ms=after['median_kernel_ms'],timer_kernel_speedup=after['kernel_speedup'],normal_full_before=normal['medians']['before'],normal_full_after=normal['medians']['after'],normal_full_kernel_speedup=normal['kernel_speedup'],normal_full_wall_speedup=normal['wall_speedup'],api_transport_measured=False),normal_summon_admission=False,normal_automatic_aim=False,multi_hit_admission=False,remaining=['Per-recipient periodic damage, bullet/finite-passive lifecycle and initialization','Delayed landing handles','Normal autonomous aim, outgoing routing and physical shot producers','Remaining characters and broad equipment/effect coverage','Whole-system efficiency after full coverage']),files))
