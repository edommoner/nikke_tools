# Storage discipline

This checkout and `.portable-recovery/runtime-resident` share the same disk.

- Before any large package, unpack, capture, benchmark, replay or restoration,
  budget peak additional **uncompressed** bytes and retain at least **20 GiB**
  free. Use the current checkout's `storage-check --required-bytes N`, including
  when executing an older immutable packet whose own default reserve is smaller.
  Do not override this reserve to squeeze a run onto a nearly full disk.
- Do not reduce suites, sample counts, comparisons or evidence to fit storage.
  Reuse saved results when identities match. A consumed claim is never a reason
  to rerun the GPU or erase evidence.
- After all readers exit, reclaim all-zero raw blocks using the CPU-only tools
  in `docs/project-storage-maintenance.md`. Current Darwin `run` does this for
  finished readbacks automatically; legacy scripts still require close-out.
  Inputs and readbacks must remain byte-identical to their historical hashes.
- Keep source snapshots, failed captures, parity/pinned buffers and archive
  receipts. Never delete `.portable-recovery/proofs`, a Git worktree, shared
  compiler/generation caches, or old archives as generic disposable output.
- For supported suites, use the established `--compact` package option and
  verify its declared test/dependency coverage. Avoid repeated source copies and
  per-packet bytecode. Never change existing immutable packets in place.
- Timing buffers may be removed only through verified lossless migration with
  a real restore test. See `docs/portable-benchmark-storage.md`. Keep archive
  payloads, inventories and receipts together when backing up or moving.

Storage operations do not certify GPU calculation results. Report both actual
filesystem free-space change and any reclaimed allocation, plus exclusions.

# Claude–Codex workflow

Claude–Codex workflow: enabled

- Claude (Claude Code) designs each unit and writes a brief; Codex CLI implements
  it in a fresh `codex exec` session; Claude verifies the diff and checks before
  committing. Procedure: Claude user skill `claude-codex-workflow`.
- Codex, when working from such a brief: edit only the allowed files, do not
  commit or push, do not expand scope or start self-directed audits, run the
  listed acceptance checks, and report changed files, commands run with results,
  and open issues. Claude is the reviewer; do not substitute your own review for it.
- Project-specific rules:
  - Never resume the old 1.2 GB desktop Codex session `01a14fa1-…`.
  - Windows work stays deferred until the user explicitly resumes it.
  - Storage discipline above applies to every unit.
