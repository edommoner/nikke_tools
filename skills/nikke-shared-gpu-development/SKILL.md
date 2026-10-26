---
name: nikke-shared-gpu-development
description: Develop and verify nikke_tools shared CUDA/Metal effects using the proof CLI, immutable packages, saved-result audits, storage checks and lossless archival, and bounded Windows checks. Use for this project's GPU development and verification workflow.
---

# NIKKE共通GPU開発

Work in the `nikke_tools` checkout. Read `docs/gpu-development-cli.md` for executable commands and package/result schemas; read the current `docs/mac-handoff.md` only when resuming implementation or deciding the next missing feature. Do not load historical reports in bulk.

## Choose the smallest useful action

- Use `python scripts/nikke_gpu.py list` to find registered short suites. Current counts and source identities belong to the CLI/package manifest, not this skill.
- Use `model-check --summary --out UNIQUE.json` for a current missing-feature audit with bounded stdout. The complete source audit stays in the output file; inspect only the relevant fields instead of loading the full historical/source report into the conversation.
- For implementation changes, extend the shared Slang runtime, Python effect definitions and native comparison cases. Use CPU preflight before GPU execution. A changed GPU source requires a deliberately verified new Metal golden; never rewrite expected hashes merely to make a check pass.
- Create an immutable package, unpack it in a fresh location, then run CPU preflight or bounded execution there. Existing verifiers write scratch files; keep those writes out of the development checkout.
- Where the checkout CLI supports it, GPU-only development after freezing a CPU contract can use `package --develop --native-baseline-package PATH` to retain expected native fingerprints. Read `docs/portable-development-expectations.md` for eligibility. Fresh run preflight and independent seal remain mandatory; this is neither a runtime oracle cache nor CUDA cache evidence. Inspect mismatches and use ordinary `--develop` only for an intentional new CPU contract.
- Run the packet’s own CLI with its unpacked root as cwd, including long `seal` runs. Keep that coordinator immutable while it runs; development edits otherwise invalidate its controller SHA. Legacy adapters also contain relative imports.
- Before transporting numerical tests, use `validation-deps --out NEW.json` in the packet to check the pinned independent oracle. The pin file travels with the packet; missing/import-incompatible dependencies stop before test workers. See project `docs/portable-python-validation-dependencies.md`; use a private dependency directory within the authorized setup scope instead of changing a shared environment or dropping tests.
- Metal runs now check Python/Swift wire agreement before CPU preparation. When extending a wire, keep the common limits, shader stride and ownership audit consistent; read `docs/portable-wire-preflight.md`. The narrowly scoped `refresh-metal-wire` writes a new packet for its reviewed pre-device failure while retaining all calculation bytes and original claims; it is not a general retry mechanism.
- If Windows snapshot diagnostics show CIM access-denied code2, inspect the saved execution permission mode before another attempt. Use the tool’s normal approval path for one read-only CPU diagnostic when authorized; do not change OS/WMI/ACL/service settings or silently skip observation. Keep successful snapshot acquisition separate from service preservation.
- Keep authoritative worktrees, captures and caches in persistent storage. Set grouped-audit TMPDIR to a persistent proof directory; temporary folders are for disposable scratch.
- Reuse saved results when source/input/runtime match. A consumed execution claim is a recovery pointer, not a reason to remove the claim or rerun the GPU. If a run failed, preserve it and decide whether a corrected source/input justifies a new package.
- For a disconnected Windows chat, request `status`/`export` for the existing capture. Do not send another `run` command. Result import/export and audit are CPU-only.
- Before sharing a Windows compile request, run the immutable packet’s own `compile-plan` with the exact artifact, level, memory and timeout. Use its passed receipt and package ID; read `docs/portable-compile-plan.md`. Sealed battle packets support CUBIN compilation; compiler diagnostic packets retain their PTX-only policy. Never substitute artifacts or edit the old packet after a policy rejection.
- Prefer the shortest CUDA suite that covers the change. Use the package's direct base-Python launch, BelowNormal priority, fresh-child JobObject, start gate and maximum 180-second command budget. Run the CPU-only Job smoke when changing orchestration; it does not require a CUDA dispatch.
- For warm CUDA validation, use `--require-cache` and its exact cache path. Add `--require-generation-cache` only for resident suites with paired reflection. Standalone probes omit resident generation-cache flags and full-world compiler certificates; do not loosen those guards to fit a probe. For cache triage use the file-only `cache-probe`; see `docs/portable-cache-preflight.md`. A hit is an advisory snapshot, never a calculation proof or a reason to skip the bounded child's cache revalidation.
- `--require-generation-cache` also checks Metal generation before CPU work. Host consumer edits may invalidate its identity even with unchanged Slang; use an explicit generation-only refresh and verify its output rather than loosening keys or retrying a consumed claim.

## Bound raw storage and preserve recovery

- Before a large benchmark, budget all uncompressed inputs/readbacks across workloads, variants, warmup and measured samples, plus a reserve. Use `python scripts/nikke_gpu.py storage-check --required-bytes N`; do not assume compression will lower the measurement peak or reduce batch/sample counts to fit. Normal GPU captures also check their prepared input/readback budget before consuming an execution claim; CPU-only checks need no GPU output allocation.
- After measurement exits, use the CPU-only workflow in `docs/portable-benchmark-storage.md` to inventory and archive timing buffers. Preserve historical evidence, failures and source snapshots; keep parity and pinned captures raw by default. Use existing authorization for removal: explicit migration removes an original only after durable archive publication, full byte-hash verification and a real restore test. Do not create historical `artifacts.json` records to fit a newer storage format.
- Check completed cleanup with `python scripts/nikke_gpu.py storage-check --storage PATH --require-archived`. This checks metadata, receipt anchors and compressed hashes without expanding every raw buffer. Use `--verify` after migration or archive changes for full decompression and retained-raw verification; reuse that result while its anchors are unchanged. A passing storage check is not a calculation or GPU proof.
- Missing archived raw during audit/replay means restore the original bytes first, never repeat GPU execution to reconstruct evidence. Keep the external archive inventory, receipts and payloads together when moving/backing up captures. Do not delete archives, automatically expire evidence, or expand cleanup to parity/pinned data outside the authorized scope.

## Preserve the proof boundaries

The canonical CPU/compiler/reference and legacy CUDA are comparison baselines. Do not modify `app/detail_gpu.py`, `app/engine_worker.py`, `app/effect_spec.py`, `app/engine_compat.py` or pinned upstream to accommodate a private GPU result unless the user explicitly changes that scope.

Metal double arithmetic uses the existing shared software binary64 design. Preserve ordered arithmetic, integer conversion boundaries and pow contracts. Generated-code normalization remains the existing strict normalizer; do not add exclusions to hide differences.

Keep calculation, containment and environment-preservation outcomes separate. Missing processes, unavailable observation, a late snapshot, or an unidentified service cannot become a successful environment-preservation result. The wrapper records its after snapshot immediately after cleanup; process cause is unknown unless independent evidence establishes it.

Static input packing, GPU admission and native-equivalent battle execution are separate coverage levels. Do not claim all characters/effects are supported from packing counts or a fixed suite. Keep explicit history omissions and capacity limits visible.

Share only the intended code/data/evidence payload, excluding personal sessions, settings, compiler distributions and raw buffers. The CLI prepares local archives; it does not authorize GitHub pushes or messages to another chat. Apply the user's actual authorization for external operations, without inventing recurring confirmation steps.

Report what changed, the checks run, unresolved differences and the next unsupported category. Use CLI timing receipts to distinguish build, execution, native comparison, observation and transfer costs. Batch documentation updates at a useful milestone.
