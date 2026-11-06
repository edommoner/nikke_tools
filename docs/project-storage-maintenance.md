# Project storage maintenance

The November 3, 2026 cleanup preserves calculation inputs, readbacks, source
snapshots, failure records, package identities, claims and the running UI.
Claude reviewed the plan and the legacy zero-block reclamation implementation.

Completed cleanup: 929 buffers / 174.4 GiB of logical bytes passed full pre/post
SHA verification; 161.0 GiB of zero-block allocation was reclaimed. Another
35,758 reproducible bytecode caches (0.75 GiB) were removed. The checkout went
from about 332 to 170 GiB, and filesystem free space from 12.8 to 174.0 GiB.
49 unanchored/unsupported paths were excluded. Existing 224 timing archives
passed their compressed-hash/preserved-metadata check. Primary/runtime unit
checks and a fresh package/unpack/storage-check succeeded without GPU runs.
The receipt is `research/project-storage-cleanup-20261103.json`; per-file
records remain under `research/portable-archives/`.

## Prevention

`portable_capture_storage.RESERVE_BYTES` is now 20 GiB in both the primary
checkout and the active runtime worktree. Run/replay budgets inherit that floor.
Package creation reserves a conservative twice-uncompressed payload plus 1 MiB;
unpack reserves the ZIP members' full uncompressed sizes, before creating the
destination. Legacy archival and restoration also retain the reserve. The CLI
allows an explicit reserve for diagnostics, but routine work must keep 20 GiB.
Immutable historical packets are unchanged: run the current checkout's
`storage-check` with their full planned write budget before using them.

On Darwin, after `run` has finished comparison, closed readers and collected
artifacts, readback zero blocks are reclaimed automatically. This runs only for
`status=finished`, not staged captures awaiting native audit. It makes no GPU
calls and leaves the saved calculation result unchanged. A failure stays in an
external `.storage-receipts/` receipt or stderr and never retries execution.
Windows keeps ordinary raw allocation.

Use supported compact packets without dropping declared tests/dependencies.
Keep one authoritative development worktree and immutable transports; do not
make another full source copy just to inspect a saved result. Packet CLIs avoid
creating new per-copy Python bytecode.

## Legacy buffers

The old primary `research/portable-build` tree predates `artifacts.json` and
`run.json` in many captures. Do not manufacture these records. The maintenance
script binds each original input/readback to its existing evidence size/SHA;
batched input sizes use the historical dispatch-header accounting.

```sh
.venv/bin/python scripts/reclaim-project-storage.py \
  --storage research/portable-archives/NEW-zero-plan --limit 2
.venv/bin/python scripts/reclaim-project-storage.py \
  --storage research/portable-archives/NEW-zero-reclaim --apply --limit 2
# After confirming real free-space recovery, resume the same apply directory:
.venv/bin/python scripts/reclaim-project-storage.py \
  --storage research/portable-archives/NEW-zero-reclaim --apply
```

The limit counts processed files, not unanchored files inspected and skipped.
Planning receipts and apply receipts use separate directories. Do not edit or
remove a failed/interrupted receipt to force a retry; inspect its diagnostic
and the source first. SIGKILL may leave an incomplete receipt; resume fails
closed with the receipt path. Each completed receipt records full SHA checks,
inode, timestamps and before/after allocated bytes. Summaries include skipped
paths and actual filesystem free space. Keep these records with the project.

The sweep excludes files modified in the last 24 hours, unfinished captures,
symlinks, hardlinks, nested Git worktrees and other filesystems. It does not
visit `.portable-recovery` or touch the live service/caches. Process and open-file
checks run before mutation, with an advisory file lock. Do not start another
writer during maintenance: advisory locks cannot exclude a non-cooperating
writer. All-zero ranges are re-read and punched in aligned chunks, then the
entire file is rehashed. Non-zero bytes, path, size, inode, atime and mtime remain;
ctime changes as required by the filesystem. Readers keep using normal raw paths
without restoration. APFS snapshots/clones can reduce actual free-space gains.

Unanchored buffers and proof-packet directories remain retained. They are not
automatically expired. Existing `portable-archives/legacy-benchmarks-20261022`
contains the only copies of previously archived timing data: never delete it.
