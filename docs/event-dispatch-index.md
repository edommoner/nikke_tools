# Ordered GPU event dispatch

The compiled effect definitions are immutable during a squad simulation. The GPU
builds a compact index once per squad: 129 offsets and at most 2,048 unsigned
16-bit definition IDs (256 definitions, eight trigger descriptors each).
Each bucket preserves the authored definition order. A definition occurs once
per event, even when multiple descriptors match that event. Descriptor matching,
activation multiplicity, conditions and trigger budgets remain in the common
executor and are re-evaluated at the same point as before.

Private periodic, forced-slot and deferred-landing continuations address their
original definition directly. HP and healing continuations retain their existing
phases. The index never changes activation order or rewrites active-instance
state. New characters use the same compiler and index without name branches.

`event_index_specs.py` describes the index independently of CUDA. The verifier
compares its ordered buckets with an independent full definition scan for all
accepted favorite-stage inputs, deduplicates identical trigger layouts, and
reads every bucket back from the GPU. Synthetic maximum-capacity and duplicate
descriptor layouts cover the bounds. Read-only probes do not advance combat.
Existing independent event, counter, HP, healing and revival oracles cover
execution ordering; new per-character battle fixtures are unnecessary for this
change. This proves dispatch behavior within the current model, not game rules
or support for previously rejected effects.

Normal GPU result metadata includes batch timing phases under
`compute.timings_ms`. `kernel_cuda` uses CUDA events around the kernel;
`kernel_launch_sync_host` includes host launch and synchronization overhead.
Packing, allocation/upload, readback and decoding have separate host timings.
These values are for the whole batch, not per-candidate latency. Module loading
and first portable-PTX JIT are outside the kernel timing. Benchmark complete
uncached API requests against identical inputs and compare damage, member and
burst outputs before attributing an improvement to the index.
