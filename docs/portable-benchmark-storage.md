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

The historical receipts shipped in `research/portable-benchmark-storage-migration.json`
and `research/portable-storage-checks.json` describe the retired branch, not a
new validation of this checkout. Their commands and counters remain historical.

From the repository root, create an inventory before removing anything:

```sh
python3.12 scripts/nikke_storage.py benchmark-inventory \
  --storage research/portable-archives/legacy-benchmarks-20261022
```

Inventory hashes every binary against both its historical evidence and the
completed report. It records retained metadata/source hashes, report snapshots,
references, original file stats, repository commit and observed free space.
Physical dispatch input sizes include extra 4-byte headers; logical saved input
sizes are derived from historical dispatch receipts, never the current ABI.
`inventory.json` and its SHA file are published together. Do not edit them.

Plan one pilot capture (no bundles or removals), keeping originals by default:

```sh
python3.12 scripts/nikke_storage.py archive-benchmarks \
  --storage research/portable-archives/legacy-benchmarks-20261022 \
  --workload all-dense-0-control
```

Add `--apply` to write bundles while keeping originals. After verifying the pilot,
remove raw copies only after lossless verification:

```sh
python3.12 scripts/nikke_storage.py archive-benchmarks \
  --storage research/portable-archives/legacy-benchmarks-20261022 \
  --apply --remove-original
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
python3.12 scripts/nikke_storage.py restore-benchmark \
  --storage research/portable-archives/legacy-benchmarks-20261022 \
  --path research/portable-build/enemy-target-scalar-benchmark-20261020T141034675819Z/all-dense-0-control/input.bin
```

Restoration identifies bytes by SHA; inode and mtime change. The original
stat fields are historical records, not restored identity. If the repository
moves, pass `--repository /new/repository` (the default is this script's root).
The stored relative paths support relocation without rewriting old evidence.

To verify all archives, retained raw files and preserved metadata:

```sh
python3.12 scripts/nikke_storage.py benchmark-status \
  --storage research/portable-archives/legacy-benchmarks-20261022 --verify
```

## Space and future runs

The CPU-only storage CLI exposes read-only checks:

```sh
python3.12 scripts/nikke_storage.py storage-check
python3.12 scripts/nikke_storage.py storage-check \
  --storage research/portable-archives/legacy-benchmarks-20261022 --require-archived
```

Use `--required-bytes N` for a planned uncompressed write budget and
`--reserve-bytes N` to increase the default 20 GiB reserve (lower values are
clamped to 20 GiB, preserving current main policy). Insufficient capacity
returns JSON with `passed: false` and exit code 2. A negative budget is rejected.
With `--storage`, metadata, receipt anchors and compressed payload hashes are
checked. `--require-archived` also fails if selected timing originals remain.
It does not require the retained parity captures to be removed. Add `--verify`
after new archival or changed archives for full decompression and retained-raw
hash checks. Fast checks leave `all_archives_verified: false`; they do not
recompute the previous full verification or make a calculation claim.

Archive creation reserves the raw file size plus compression overhead and a
20 GiB reserve, without assuming compressibility. Restore reserves the expanded
size plus 20 GiB. Only one raw temporary is restored at a time. All data paths
must be regular files with one hard link; symlinks, hardlinks, unsafe paths,
changed evidence and concurrent migrators are rejected. The CLI checks for
benchmark/verification processes; this is a local best-effort check, not a lock
against programs that ignore it. If process observation is unavailable, the
operation stops before changing raw data. Do not start a benchmark during migration. `--repository PATH` selects a different
repository for every benchmark subcommand. Even planning takes the adjacent
`.lock` file; it writes no bundles, inventory, journal, or raw files.
Inventory is an explicit metadata-writing command. Restore writes the requested
path and a journal; it never overwrites an existing file.

For a future completed run, inventory its actual folder and
report, then use `archive-benchmarks --apply` as above:

```sh
python3.12 scripts/nikke_storage.py benchmark-inventory \
  --storage research/portable-archives/NEW-RUN \
  --folder NEW-CAPTURE-FOLDER --report COMPLETED-REPORT.json
```

This prevents silent disk exhaustion and retains compact completed results;
it does not reduce the peak storage needed during measurement. There is no
automatic expiry, deduplication, hardlink conversion or parity-buffer removal.
Freed filesystem space can differ from raw-byte totals because of APFS snapshots
or concurrent activity; the final report records both figures.
