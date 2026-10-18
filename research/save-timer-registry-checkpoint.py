from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
reports=['research/timer-registry-'+n+'.json' for n in ('native','ptx','instant-native','staged-native','unit','order-native','batch-native','coverage','owned-api','after','normal-performance','periodic-native')]+['research/runtime-wiring.json']
performance=reports[9:11]
r=checked_receipts([p for p in reports if p not in performance])
experiment=read('research/timer-registry-index-experiment.json');assert experiment['passed'] and experiment['adopted'] is False
for path in performance:
    report=read(path);assert report['passed'];r[path]=report
    for source,digest in report['source_sha256'].items():
        assert any((ROOT/a/source).is_file() and sha(a+'/'+source if a else source)==digest for a in ('','research/ports/v81-timer-index-experiment')),('experiment provenance',source)
workspace=None
for path in reports[:2]:
    assert len(r[path]['cases'])==8
    sizes={c['workspace_bytes'] for c in r[path]['cases']};assert len(sizes)==1
    size=sizes.pop();assert size==1260136
    if workspace is not None:assert size==workspace
    workspace=size
assert len(r[reports[2]]['cases'])==6 and len(r[reports[3]]['cases'])==9
assert r[reports[4]]['tests_run']==112 and len(r[reports[5]]['cases'])==25 and r[reports[6]]['batch_squads']==10
assert r[reports[7]]['existing_programs_identical']==187
assert r[reports[8]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[8]]['mode_policy_roundtrip']['passed']
after=r[reports[9]];before=read('research/timer-registry-before.json')
assert after['interleaved'] and after['family']=='damage' and len(after['samples'])==len(after['old_samples'])==5
assert before['stimulus_sha256']==after['stimulus_sha256'] and before['semantic']==after['semantic']
normal=r[reports[10]];assert normal['interleaved'] and normal['batch_squads']==8
assert len(r[reports[11]]['cases'])>=12
for manifest,binary,digest in [('app/detail_effects-sm86.json','app/detail_effects-sm86.cubin','binary_sha256'),('app/detail_effects-build.json','app/detail_effects.ptx','ptx_sha256')]:
    m=read(manifest);assert m['abi']=='detail_timer_registry_v81' and m['source_sha256']==sha('app/detail_effects.cu') and m[digest]==sha(binary)
stage='research/ports/v81-timer-registry-native-stage'
for source,digest in before['source_sha256'].items():
    assert any((ROOT/a/source).is_file() and sha(a+'/'+source if a else source)==digest for a in ('',stage)),('baseline provenance',source)
files=reports+['research/timer-registry-index-experiment.json','research/timer-registry-before.json','research/timer-registry-native-stage.json.receipt','research/benchmark-periodic-targets.py','research/benchmark-periodic-normal.py','research/save-timer-registry-checkpoint.py','research/checkpoint_receipts.py','README.md','docs/timer-registry.md','docs/adding-effects.md','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json','app/periodic_target_runtime.py','app/timer_registry_runtime.py','scripts/timer_registry_cases.py','scripts/verify-timer-registry-detail.py','tests/test_timer_registry_runtime.py','scripts/verify-common-runtime-unit.py']
files+=['docs/summon-source-next-steps.md']
print(save_checkpoint('research/timer-registry-checkpoint.json','research/ports/v81-timer-registry-verified',dict(passed=True,objective_complete=False,abi='detail_timer_registry_v81',workspace_bytes=workspace,stage_workspace_bytes=1260136,workspace_saved_bytes=0,shared_cases_per_backend=8,existing_instant_cases=6,existing_staged_cases=9,lightweight_methods=112,ordering_cases=25,mixed_squads=10,existing_programs_identical=187,efficiency=dict(adopted=False,experiment='research/timer-registry-index-experiment.json',before_kernel_ms=after['before_kernel_ms'],experimental_kernel_ms=after['median_kernel_ms'],experimental_kernel_speedup=after['kernel_speedup'],normal_medians=normal['medians'],experimental_normal_kernel_speedup=normal['kernel_speedup'],experimental_normal_wall_speedup=normal['wall_speedup']),normal_summon_admission=False,per_recipient_damage_clocks=False,remaining=['Per-recipient damage clocks and carrier lifetimes','Generation-bound delayed landings and autonomous enemy routing','Remaining character/equipment/special-effect coverage','Whole-system efficiency after full support']),files))
