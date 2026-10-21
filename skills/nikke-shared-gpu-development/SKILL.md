---
name: nikke-shared-gpu-development
description: Develop and verify nikke_tools shared CUDA/Metal effects and execution using the repository proof CLI, immutable verification packages, saved-result audits, and bounded Windows checks. Use for this project's GPU migration and verification workflow.
---

# NIKKE共通GPU開発

Work in the `nikke_tools` checkout. Read `docs/gpu-development-cli.md` for executable commands and package/result schemas; read the current `docs/mac-handoff.md` only when resuming implementation or deciding the next missing feature. Do not load historical reports in bulk.

## Choose the smallest useful action

- Use `python scripts/nikke_gpu.py list` to find registered short suites. Current counts and source identities belong to the CLI/package manifest, not this skill.
- For implementation changes, extend the shared Slang runtime, Python effect definitions and native comparison cases. Use CPU preflight before GPU execution. A changed GPU source requires a deliberately verified new Metal golden; never rewrite expected hashes merely to make a check pass.
- Create an immutable package, unpack it in a fresh location, then run CPU preflight or bounded execution there. Existing verifiers write scratch files; keep those writes out of the development checkout.
- Reuse saved results when source/input/runtime match. A consumed execution claim is a recovery pointer, not a reason to remove the claim or rerun the GPU. If a run failed, preserve it and decide whether a corrected source/input justifies a new package.
- For a disconnected Windows chat, request `status`/`export` for the existing capture. Do not send another `run` command. Result import/export and audit are CPU-only.
- Prefer the shortest CUDA suite that covers the change. Use the package's direct base-Python launch, BelowNormal priority, fresh-child JobObject, start gate and maximum 180-second command budget. Run the CPU-only Job smoke when changing orchestration; it does not require a CUDA dispatch.

## Preserve the proof boundaries

The canonical CPU/compiler/reference and legacy CUDA are comparison baselines. Do not modify `app/detail_gpu.py`, `app/engine_worker.py`, `app/effect_spec.py`, `app/engine_compat.py` or pinned upstream to accommodate a private GPU result unless the user explicitly changes that scope.

Metal double arithmetic uses the existing shared software binary64 design. Preserve ordered arithmetic, integer conversion boundaries and pow contracts. Generated-code normalization remains the existing strict normalizer; do not add exclusions to hide differences.

Keep calculation, containment and environment-preservation outcomes separate. Missing processes, unavailable observation, a late snapshot, or an unidentified service cannot become a successful environment-preservation result. The wrapper records its after snapshot immediately after cleanup; process cause is unknown unless independent evidence establishes it.

Static input packing, GPU admission and native-equivalent battle execution are separate coverage levels. Do not claim all characters/effects are supported from packing counts or a fixed suite. Keep explicit history omissions and capacity limits visible.

Share only the intended code/data/evidence payload, excluding personal sessions, settings, compiler distributions and raw buffers. The CLI prepares local archives; it does not authorize GitHub pushes or messages to another chat. Apply the user's actual authorization for external operations, without inventing recurring confirmation steps.

Report what changed, the checks run, unresolved differences and the next unsupported category. Use CLI timing receipts to distinguish build, execution, native comparison, observation and transfer costs. Batch documentation updates at a useful milestone.
