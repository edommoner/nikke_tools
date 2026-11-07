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

## Current CPU-only CLI

The cleanup figures and `research/project-storage-cleanup-20261103.json` are
historical evidence from the retired branch. They do not claim a new cleanup,
automatic post-run maintenance, or package/run integration on current main.
Historical source hashes identify the old implementation and remain unchanged.

Before large copies or restoration, run:

```sh
python3.12 scripts/nikke_storage.py storage-check --required-bytes N
```

The CLI retains main's 20 GiB capacity floor; `--reserve-bytes` can raise it.
Archive creation budgets the uncompressed file plus compression overhead;
restoration budgets the full expanded file. Keep at least 20.5 GiB free for
this port's validation. Storage checks do not certify calculation results.

Finished captures with artifacts/run metadata can use the existing manual
`sparsify-raw --capture PATH --out EXTERNAL-RECEIPT` command. Add `--apply`
to reclaim allocation. There is no automatic run hook in current main.

## Legacy buffers

The old primary `research/portable-build` tree predates `artifacts.json` and
`run.json` in many captures. Do not manufacture these records. The maintenance
script binds each original input/readback to its existing evidence size/SHA;
batched input sizes use the historical dispatch-header accounting.

```sh
python3.12 scripts/nikke_storage.py reclaim-project \
  --storage research/portable-archives/NEW-zero-plan --limit 2
python3.12 scripts/nikke_storage.py reclaim-project \
  --storage research/portable-archives/NEW-zero-reclaim --apply --limit 2
# After confirming real free-space recovery, resume the same apply directory:
python3.12 scripts/nikke_storage.py reclaim-project \
  --storage research/portable-archives/NEW-zero-reclaim --apply
```

`--repository PATH` selects the repository root (default: this checkout). The
sweep only visits its `research/portable-build` tree. Planning hashes files and
writes external planning receipts and a summary, with zero allocation reclaimed.
Files with less than 1 MiB allocated are omitted from scanning.

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
