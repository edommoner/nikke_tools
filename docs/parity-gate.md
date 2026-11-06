# Native / canonical CPU parity gate

Use Python 3.12+ from this worktree. The CLI compares **decoded** native payloads with canonical `engine_worker.evaluate(body)` payloads using the product's unchanged `portable_detail.payload_differences`. Raw internal kernel counters do not affect this comparison. No kernel or product behavior is changed.

```sh
export NIKKE_SLANG_ROOT=/path/to/slang-2026.20-Darwin-arm64
python3.12 scripts/parity-gate.py build-corpus
python3.12 scripts/parity-gate.py run --output research/parity/runs/initial
python3.12 scripts/parity-gate.py run --output research/parity/runs/next \
  --previous research/parity/runs/initial/summary.json
python3.12 scripts/parity-gate.py build-corpus --include-character 에밀리아 --count 20 \
  --output research/parity/emilia.json
python3.12 scripts/parity-gate.py run --corpus research/parity/emilia.json \
  --output research/parity/runs/emilia --previous research/parity/runs/next/summary.json
```

`build-corpus` reproduces S2's `ROWS` / `BASE`: S1 result IDs/members plus the benchmark's complete body and S1 settings. The original S1 benchmark path must exist at construction time; `--benchmark PATH` supplies a relocated/current JSON array. The resulting corpus has no runtime dependency on that path. New squads have unique bodies, always contain the requested Korean canonical name, and use seed `20261106` by default. Existing growth entries are preserved; a newly released character absent from the benchmark uses the canonical complete default growth entry. Supply a benchmark containing the desired growth to override it. Corpus/cache/run artifacts live in ignored `research/parity/`.

`run` defaults to 10 process workers and deferred native verification. CPU evaluation runs in a fresh process per request, as required by the canonical adapter. Disposable native transport captures are removed after decoding; compressed native payloads and an fsynced result journal and an exclusive run lock make the run resumable. Repeat the **same command and output directory** after interruption. Use a new directory for each subsequent comparison. A changed corpus, reference identity, native source, or sampling policy requires a new run directory; completed cache entries remain reusable. Do not edit calculator/data/kernel files during a run. A storage preflight compiles request layouts to budget the ten largest simultaneous captures plus 1 GiB overhead and requires 20 GiB free beyond that budget. The reserve is checked as workers complete as well.

## CPU cache identity

Canonical request JSON uses the product record's `ensure_ascii=False`, sorted keys, compact separators, and `allow_nan=False`. The cache filename is SHA-256 over this request digest, code identity, member/global data identity, and cache schema. Gzip entries include the identity, complete CPU payload, and payload digest; writes are atomic and corrupt entries fail explicitly. Keys are cache keys, never build guards or source pins.

Code identity comes from an AST import closure rooted at `engine_worker.py` and all upstream `calculator/*.py`. It follows imports inside functions, relative imports and literal dynamic compatibility-layer names (`effect_spec.COMPAT_LAYERS`). Optional CPU reference models are included conservatively. Only the worker's GPU compile, portable static-input/audit, and event-only entry points are excluded. The actual source inventory is saved in each run's `manifest.json`; the current tree yields 143 files. Third-party interpreter/library changes are outside this source identity; use a new cache directory when changing that environment.

Data slicing follows `runner.spec`, `calculator.base_stat`, `calculator.buff_manager`, `calculator.timeline`, and `effect_overrides`:

| Table | Member slice | Global/shared part |
| --- | --- | --- |
| `parsed_nikke.json`, `parsed_skills.json`, `char_defaults.json` | Full entries for all five names, including all skill variants | Underscore metadata/rules |
| `weapon_delays.json`, `burst_gauge.json` | Five names in `_exceptions` | All other keys |
| `engine-effect-overrides.json` | Ordered corrections for those five names | Other top-level fields |
| `parsed_nikke.json` derived ranges | — | Exact modal range per weapon, with the calculator's frequency/tie-break rule |
| Other upstream/repo `data/**/*.json` | — | Whole file content, conservatively |

Full skill entries cover favorite-item variants and linked effects. The derived range table matters because weapon swaps can use a roster-wide modal range: an unrelated character can legitimately change this shared input. Harmless additions that leave the derived ranges unchanged preserve other squads' identities. Boss presets/scripts, tactics, weapon mechanics (including character lists), growth/base-stat/cube/equipment tables, import/display mappings and unknown future JSON tables remain global because safe slicing is not established. `engine-revisions.json` is an installation-integrity manifest, not calculation data; its represented calculator/data contents are covered directly. Importer-only scraper source JSON is not an evaluation input: its resource-name map is used for import/catalog display, not `evaluate` results.

## Reference changes and results

With `--previous SUMMARY`, a changed member slice always requires a current CPU reference. When code/global data changes, unchanged-member squads are sampled deterministically (default `--sample-fraction 0.1`, rounded up). Remaining squads compare against their previous cached CPU payload and are labelled `inherited-from-previous-reference`. Inheritance follows the actual old reference key through multiple generations; missing old payloads trigger CPU evaluation. Inherited comparisons are counted separately from current-reference comparisons and **are not fresh verification of the changed reference**. `--full` recomputes every CPU payload, even current cache hits. Without a previous summary, absent references must all be computed.

`summary.json` contains matched/mismatched (with exact `differing_fields`), CPU fallback/unsupported counts, cache hits/misses and CPU evaluation counts, per-entry/total compressed size, wall time, per-character mismatch/inheritance tables, new matches and regressions. Previous rows are joined by full request digest, not positional ID. A previous match becoming any non-match is a regression. Without a previous run, mismatches are new findings. Regressions and unsupported/fallback conditions exit nonzero; known unchanged mismatches with a named baseline do not. Canonical exceptions stop the run and preserve progress. Counts and elapsed time on a resumed run describe its accumulated results; `manifest.json.sessions` checkpoints invocation timings. An interrupted session retains its last completed-row timing (a lower bound).

An initial seed costs a full CPU census. Following unchanged-reference runs perform native computation and load compressed CPU payloads, with zero CPU battle evaluations. Keep the cache to avoid paying the seed again; no automatic eviction is performed.

## Mechanism-pair corpus (S6)

```sh
python3.12 scripts/parity-gate.py build-corpus --cover mechanism-pairs \
  --output research/parity/corpus.json
python3.12 scripts/parity-gate.py build-corpus --cover mechanism-pairs \
  --multiplicity 2 --output research/parity/pairs-k2.json
python3.12 scripts/parity-gate.py build-corpus --extend-for-character 에밀리아 \
  --corpus research/parity/corpus.json --output research/parity/emilia.json
python3.12 scripts/parity-gate.py run --require-cache \
  --output research/parity/runs/next --previous research/parity/runs/initial/summary.json
```

Schema 2 stores `base` once, then ordered `members`, top-level `overrides`, and the original `request_sha256` per squad. Reconstruction is a shallow top-level overlay followed by `squad=members`; nested objects are replaced whole. Every reconstructed request is checked against its saved hash before use. `.json.gz` is also supported. Schema 1 full-body corpora remain readable. Migration does not change CPU cache keys. `--include-character NAME --count N --corpus EXISTING` also appends deterministic, burst-valid squads to an existing corpus.

`app/parity_corpus.py` calls the real `portable_detail.prepare` and `compile_product`, without CPU battle execution. It extracts per-owner features from the **compiled wire**, not skill prose or character-name lists. Addresses and strides of all `definition_*` accessors are discovered from `gpu/definition_runtime.slang`, using `portable_specs.LIMITS/FIELDS`; an unrecognized accessor fails construction. The adjacent descriptor layouts come from `portable_trigger_specs.pack_descriptors`, `portable_recipient_specs.pack`, and `portable_resource_specs.pack`. The output companion `CORPUS.features.json` contains every discovered reader/address, actual compiler context, character feature multiset, and coverage counts.

| Vocabulary | Compiled source / kernel consumer | Representation |
| --- | --- | --- |
| `kind`, `stat`, `event`, `countMode`, `target`, `stageArg`, `stageOverride`, `damageRoute`, `healthScaling`, `enemyBuff`, `polarity`, `buffEvent` | Definition readers; admission, dispatch, quantity, damage and health runtimes | Exact integer codes; no guessed character roles |
| `flags`, `damageFlags`, `quantityFlags`, `periodicFlags`, `alliedFlags`, `mergeEligible`, `queryResolve` | Definition/recipient readers | Individual set bits (recipient packed subfields decoded first) |
| `value`, `duration`, `interval`, `period`, `fixedValue`, `damageGauge` | Binary64 Definition readers | Negative / zero / one / greater-than-one (positive fractions share `many`); magnitudes are not identities |
| Remaining count/switch readers, including `maxStack`, `budget`, `immediate`, `preserve`, `reentry`, `toggle`, `triggerCount`, `conditionCount`, `damageCount/Hits/Normal/Pending`, `pendingHits`, `bulletDuration/Bound`, `durationCast`, `exclusive`, `fixedLiteral` | Corresponding Definition readers | Negative / zero / one / many |
| Name/group fields, `recipients`, `statKey` | Local allocation IDs / masks | Presence only; local numeric IDs and character masks are not mechanism identities |
| `trigger:event`, `trigger:count-mode`, `trigger:stage` | All active 8-word EVENT descriptors | Exact codes, including signed stage/HP-edge modes |
| `condition:type` | All active 4-word CONDITION descriptors | Exact predicate code (HP, gauge, stack, probability, etc.) |
| `recipient:kind`, `recipient:count` | RECIPIENT plus all union child nodes | Exact selector mode; count bucket. Includes random, rank, exclusion, HP/cover reads and ordered selection |
| `resource:operation`, `resource:flag` | RESOURCE_DEFINITION | Exact operation and individual flags |
| `weapon:mode-change`, `weapon:type` | MODE bank and compiled static weapon metadata | Nonempty mode declaration; weapon family |
| `setting:burst_gauge_mode`, `setting:burst_policy`, `enemy:code` | Actual request settings | Literal setting value |

This is **static mechanism presence**, not dynamic branch/timing coverage. A character can carry a dormant condition. Numerical boundaries, exact named/exclusion-set equality, ordering and whether two mechanisms execute at the same instant are not proved by pair coverage. Features are settings/growth scoped: compilation uses the S1 base settings and profile, including boss preset, enemy configuration and equipment. Each character has one deterministic complete, burst-valid compiler context; static masks are normalized to presence to avoid turning the vocabulary back into character identities. Context-sensitive compiler changes require rebuilding. Unknown numeric distinctions outside these categories are not certified. Feature-cache identities include compiler/kernel/extractor sources, CPU/data identities, complete base settings, and roster.

A pair is unordered and includes `(f,f)` when two compiled definitions (or two owners) supply the same mechanism. Per-owner multiplicities are capped at two. Every pair of feature owners fits in five distinct members: add at most one member each of burst stages 1, 2 and 3, then fill remaining slots. The constructor checks real S1 distinctness and burst coverage, with an all-stage (`A`) member able to fill one missing stage. The target universe is therefore all feasible pairs over this roster and these settings, not merely pairs present in a random candidate pool.

Candidate squads start with burst-valid S1 squads and a deterministic random pool. Missing pairs receive constructive witnesses; extra members are chosen for additional uncovered pairs. Greedy set cover selects the largest marginal gain repeatedly from that completed pool. This is deterministic for a fixed seed and inputs; it is not a claim of a globally minimum corpus. `--multiplicity k` requires k distinct ordered squads for every pair. The report also computes the original 2,460-squad S1 pair coverage, including its unconstrained C cohort, for comparison. IDs of reused S1 squads are retained; new IDs start after S1.

Extension targets every pair involving a feature carried by the named character, credits existing corpus coverage, and adds only greedy witnesses for outstanding pairs. It always adds at least `--minimum-character-squads` new squads (default 3), even if all mechanisms were covered already. Existing requests are preserved, including profile entries. A character missing from the profile receives canonical growth defaults. A real release may change global tables or modal weapon ranges; the CPU reference-change policy still applies independently of corpus coverage.

For native-only historical validation, `run --native-root SNAPSHOT --require-cache` compiles/executes GPU sources and `scripts/native-product-host.cpp` from that disposable archive. Current Python, compiler preparation and CPU/data identities remain in use. The normal product decoder and comparison remain unchanged. `--require-cache` checks every current CPU entry before native execution. Use a new run directory per snapshot. Retain archive audits and verify `git diff OLD HEAD -- app research/upstream` is empty before interpreting historical comparisons.

## Python line coverage and selective reuse (S8)

Every fresh reference, including `--full`, now starts CPython 3.12 global
`sys.monitoring.events.LINE` monitoring **before importing any code-identity
module**. A worker fails explicitly if any such module is already in
`sys.modules`. CPU work precedes native preparation in each fresh process;
`max_tasks_per_child=1` remains mandatory. The callback records presence and
returns `sys.monitoring.DISABLE`; repeated execution of a location is unnecessary.
Coverage includes the complete source closure, including app layers and import-time
functions, rather than just calculator files.

The existing schema-1 payload entry is unchanged. Adjacent `<key>.cov.json.gz`
files contain `cache_key`, the original code-identity file/hash mapping, and
`lines: {relative_path: [sorted line numbers]}`. Each source version is retained
once as `CACHE/sources/<sha256>.gz`. Source and coverage writes use atomic
replacement; absent sidecars or source versions prevent cross-code reuse.
Existing entries and source versions are retained, without automatic deletion.

When a current entry is missing, the gate considers older entries with exactly
the same complete request and member/global data identity. `source_changes` is a
pure AST comparison of original and current source versions:

* Added/removed files or a changed module skeleton invalidate every request.
  The skeleton replaces bodies of top-level functions and methods directly in
  top-level classes with placeholders. Signatures, decorators, defaults, class
  attributes and module statements remain significant.
* Otherwise, changed function/method bodies invalidate only references whose
  original coverage intersects the original body range, starting at the first
  body statement and ending at the last statement's `end_lineno`. The `def`
  line is excluded. Nested functions belong to the enclosing body.
* Comments, whitespace and shifted line numbers alone do not change AST dumps.
  Docstrings count as body changes. Unparseable or ambiguously duplicated
  definitions conservatively invalidate the file's entries.

Valid payloads receive `reference_status: coverage-reused`. Their new cache
entries record `reused_from` pointing to the **original** entry; subsequent
identity changes always compare original sources and original coverage with the
current sources, never intermediate line coordinates. Direct hits on aliases
are ordinary cache hits. Rows that cannot reuse record `invalidating` file and
function reasons. Entries without coverage retain the existing previous-run
inherit/sample policy; inheritance remains a separate status and claim.

`--coverage-spot-check FRACTION` defaults to `0.02`. A stable hash of the existing
seed and request selects each coverage reuse with that probability (use `1` to
check every reused row). A selected row evaluates afresh with monitoring before
native execution; a digest disagreement increments `spot_check_failures`, does
not publish an alias, and exits nonzero even if the native comparison matches.
The summary reports `fresh`, `cache_hits`, `coverage_reused`, `spot_checked`, and
`spot_check_failures`. Fresh and spot-check comparisons against an older
same-request/data entry also record diagnostic `previous_code_payload_equal`
and the compared original key; summary true/false counts do not affect status.

CPU spot checks and `previous_code_payload_equal` compare payload digests after
excluding only the top-level `evaluator` git-provenance key. All other fields,
including nested `evaluator` keys, remain significant. Stored payloads retain
provenance, and `payload_sha256`, cache integrity and exact-copy alias checks
continue to cover the full payload. The gate's native-vs-cached-CPU comparison
also removes only top-level `evaluator` from copies before calling the unchanged
product `payload_differences`. Each row records `provenance_differs`, and the
summary counts these rows, so provenance differences remain visible without
causing parity mismatches. The product's same-process CPU verification is unchanged.

This is conservative selection under a static Python source model, not a proof
for dynamic `exec`/`eval`, third-party or interpreter changes. Changes to those
environments require a separate cache. Data changes have no line coverage and
keep the existing identity/inherit/sample policy. Executed source generated by
compatibility AST rewriting can share original filenames/locations; line traces
do not identify generated source text independently.

For the S8 smoke only, the internal Python argument
`coverage_test_code_root` can point at a disposable source-only tree to inject
identity/body changes while executing the worktree's unchanged evaluator. This
is deliberately not a CLI flag. It requires a separate cache, is labelled in the
run manifest, and is a test of invalidation/reuse mechanics, not execution of the
modified sources. The S8 harness uses inert `pass` additions on existing lines
and a comment-only identity edit; it never modifies upstream in the worktree.
