# Legacy benchmark buffer storage

The two October 20 benchmark folders contained 121.4 GiB of raw inputs and
readbacks. Only timing captures are eligible for archival; `full-*` parity
captures and externally referenced captures stay raw. All evidence, summaries,
failure records and captured source files remain unchanged. This operation
uses no GPU and does not certify a calculation result.

Completed on October 22, 2026 (Japan time): 224 timing files / 105.0 GiB were
archived to 325.2 MiB of gzip payload (392.0 MiB allocated for the complete
archive directory). Observed filesystem free space increased by 104.6 GiB,
from 7.4 to 112.0 GiB. All 224 archives were independently decompressed and
verified after migration; 24 parity binaries and 485 metadata/source/report
files matched their inventory hashes. The 26 storage-related tests passed.
The machine-readable receipt is
[`portable-benchmark-storage-migration.json`](../research/portable-benchmark-storage-migration.json).

The local inventory and gzip bundles live under
`research/portable-archives/legacy-benchmarks-20261022/` (Git-ignored).
**Keep this directory:** it contains the only retained copies of buffers whose
raw files have been removed. Moving or backing up the repository must include
both `portable-build` and `portable-archives`.

## Commands

From the repository root, create an inventory before removing anything:

```sh
.venv/bin/python scripts/archive-portable-benchmarks.py inventory \
  --storage research/portable-archives/legacy-benchmarks-20261022
```

Inventory hashes every binary against both its historical evidence and the
completed report. It records retained metadata/source hashes, report snapshots,
references, original file stats, repository commit and observed free space.
Physical dispatch input sizes include extra 4-byte headers; logical saved input
sizes are derived from historical dispatch receipts, never the current ABI.
`inventory.json` and its SHA file are published together. Do not edit them.

Archive one pilot capture, keeping originals by default:

```sh
.venv/bin/python scripts/archive-portable-benchmarks.py migrate \
  --storage research/portable-archives/legacy-benchmarks-20261022 \
  --workload all-dense-0-control
```

After verifying the pilot, remove raw copies only after lossless verification:

```sh
.venv/bin/python scripts/archive-portable-benchmarks.py migrate \
  --storage research/portable-archives/legacy-benchmarks-20261022 \
  --remove-original
```

Every file is compressed and fully decompressed to its expected SHA before the
bundle is published. Archive and receipt are published as one directory. A
separate read verifies the published bundle, followed by a real restore to a
temporary file and another SHA check. Only then can the unchanged raw file be
unlinked. The raw directory is synced and a durable journal records removal.
Existing valid bundles are verified and reused on restart; missing raw files
are accepted only if a valid bundle exists. No benchmark is re-run for recovery.
Temporary compressed/restored copies left by a killed migration are cleaned on
restart while holding the migration lock. Corrupt published bundles stop the
operation; their originals, if present, are retained.

Before consuming an archived input/readback with an older verifier, restore
that exact path. Existing files are never overwritten:

```sh
.venv/bin/python scripts/archive-portable-benchmarks.py restore \
  --storage research/portable-archives/legacy-benchmarks-20261022 \
  --path research/portable-build/enemy-target-scalar-benchmark-20261020T141034675819Z/all-dense-0-control/input.bin
```

Restoration identifies bytes by SHA; inode and mtime change. The original
stat fields are historical records, not restored identity. If the repository
moves, pass `--repository /new/repository` (the default is this script's root).
The stored relative paths support relocation without rewriting old evidence.

To verify all archives, retained raw files and preserved metadata:

```sh
.venv/bin/python scripts/archive-portable-benchmarks.py status \
  --storage research/portable-archives/legacy-benchmarks-20261022 --verify
```

## Space and future runs

The common proof CLI now exposes read-only checks:

```sh
.venv/bin/python scripts/nikke_gpu.py storage-check
.venv/bin/python scripts/nikke_gpu.py storage-check \
  --storage research/portable-archives/legacy-benchmarks-20261022 --require-archived
```

Use `--required-bytes N` for a planned uncompressed write budget and
`--reserve-bytes N` to change the default 20 GiB reserve. Insufficient capacity
returns JSON with `passed: false` and exit code 1. A negative budget is rejected.
With `--storage`, metadata, receipt anchors and compressed payload hashes are
checked. `--require-archived` also fails if selected timing originals remain.
It does not require the retained parity captures to be removed. Add `--verify`
after new archival or changed archives for full decompression and retained-raw
hash checks. Fast checks leave `all_archives_verified: false`; they do not
recompute the previous full verification or make a calculation claim.

Normal `nikke_gpu.py run` automatically records `storage.json` after CPU
preflight and before the exclusive GPU claim: the budget covers prepared input
plus the actual output layout's uncompressed readback and the reserve. A failed
budget starts no GPU child and consumes no claim. Compiler/native scratch and
other concurrent writes may need additional capacity. `--cpu-only` and
`--smoke` do not reserve an unused GPU output. Replay checks the bytes it will
copy before creating its destination. Audit/replay missing-raw errors direct the
operator to restore, without automatically retrying a GPU execution.

The benchmark-storage fault/restore tests are registered in the regression
CPU checks, alongside existing capture-storage checks. The tracked package
payload must include these tests and their helper module before packaging.

Archive creation reserves the raw file size plus compression overhead and a
20 GiB reserve, without assuming compressibility. Restore reserves the expanded
size plus 20 GiB. Only one raw temporary is restored at a time. All data paths
must be regular files with one hard link; symlinks, hardlinks, unsafe paths,
changed evidence and concurrent migrators are rejected. The CLI checks for
benchmark/verification processes; this is a local best-effort check, not a lock
against programs that ignore it. Do not start a benchmark during migration.

The two legacy benchmark scripts now preflight the full uncompressed run using
their own ABI and suite counts, before writing captures. Neither sampling nor
GPU timing is changed. Compression is a separate command after the benchmark
process has exited. For a future completed run, inventory its actual folder and
report, then use the same migrate command:

```sh
.venv/bin/python scripts/archive-portable-benchmarks.py inventory \
  --storage research/portable-archives/NEW-RUN \
  --folder NEW-CAPTURE-FOLDER --report COMPLETED-REPORT.json
```

This prevents silent disk exhaustion and retains compact completed results;
it does not reduce the peak storage needed during measurement. There is no
automatic expiry, deduplication, hardlink conversion or parity-buffer removal.
Freed filesystem space can differ from raw-byte totals because of APFS snapshots
or concurrent activity; the final report records both figures.
