from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/timer-registry-after.json','research/timer-registry-normal-performance.json']
r=checked_receipts(reports);after=r[reports[0]];normal=r[reports[1]]
assert after['interleaved'] and normal['interleaved']
files=reports+['app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','research/benchmark-periodic-targets.py','research/benchmark-periodic-normal.py','research/apply-timer-index.py','research/save-timer-index-experiment.py']
print(save_checkpoint('research/timer-registry-index-experiment.json','research/ports/v81-timer-index-experiment',dict(passed=True,objective_complete=False,adopted=False,workspace_bytes=1259120,functional_workspace_bytes=1260136,reason='Small memory saving with no kernel improvement in timer workload and slower median normal full calculation; restore the verified shared executor.',timer_kernel_before_ms=after['before_kernel_ms'],timer_kernel_after_ms=after['median_kernel_ms'],normal_medians=normal['medians'],kernel_speedup=normal['kernel_speedup']),files))
