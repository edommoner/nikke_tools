# S9: learned surrogate for squad search

Research only; native detailed rankings are unverified (`verify_detail=false`, deferred verification). No CPU reference or fallback runs.

## Method

S1 benchmark profile and settings are reused unchanged: 206 characters, 180 s, level 400, DEF 31784, wind, 50 px core, 25 m, auto burst, fixed gauge. The unchanged S1 Node adapter supplies tool environment only; it is not invoked per squad. Uniform ordered samples use `random.sample(names, 5)` and reject missing burst coverage (the S1 rule), exact ordered duplicates and S1 rows. Dataset seed 44; search seed 46. Each A-stage member covers one otherwise missing stage. Ordering is sampled uniformly and retained.
Native `portable_detail.evaluate_many` uses batches of 32 (last search batch 12), 10 host threads, deferred verification. Pending fallbacks are copied to JSONL and excluded; the fallback entry points are guarded against reference execution. JSONL is append-only and flushed/fsynced per batch; restart checks member identity and skips saved IDs. Only owned temporary capture directories are removed after result extraction. Warm native caches are copied into scratch to keep adapter writes inside the allowed scope. No throughput optimization was made.

## Part A: first 320 squads

Timers wrap the existing Python preparation, compiler, decoder, native execute and native host calls. Host-reported kernel seconds are counted once per physical dispatch. Dispatch includes build-cache checks, transport, readback and digests; host process includes launch and host I/O. These nested measurements must not be added twice. End-to-end includes extraction and cleanup, excluding JSONL output and one-time setup/cache copying. Concurrent dispatch, host-process and kernel timings are summed work durations and overlap. The native-and-adapter residual is elapsed time minus serial preparation, compile, decode and cleanup; it includes transport critical path and remaining Python/I/O. It cannot separate kernel critical-path time from transport overhead without changing the adapter. dispatch_outside_host and host_outside_kernel are differences of summed call durations, not additional elapsed components.

| Component | ms/squad |
|---|---:|
| prepare | 10.0673 |
| compile | 14.7332 |
| host_process | 235.8586 |
| dispatch | 333.1067 |
| decode | 2.8553 |
| cleanup | 1.3831 |
| kernel | 219.0466 |
| end_to_end | 128.8579 |
| native_and_adapter_residual | 99.8191 |
| dispatch_outside_host | 97.2482 |
| host_outside_kernel | 16.8119 |

Largest elapsed-time component (dispatch and adapter overhead grouped by residual): **native_and_adapter_residual**. Node time in these batches: 0 (one environment lookup occurs before evaluation).

## Counts and storage

Dataset: 12000 generated; 11956 native successes. Backends: {'native_detail': 11956, 'native_failed': 44}.
Train / holdout: **10000 / 1956** successful rows. Native failures make a 10,000/2,000 successful split impossible from exactly 12,000 generated rows; preserve 10,000 train and reduce holdout. Split: seed45 shuffle successful rows; first 10000 train, remaining holdout.
S1 native successes form a separate external test set, reported both together and by A/B/C. A is template-selected and C lacks the burst constraint, so neither matches the random covered sampling distribution.

| Failure reason | Dataset squads |
|---|---:|
| Named modifier carriers require their checked ordinary BODY product entry | 12 |
| Ordinary lock markers require their checked BODY/ADD product composition | 5 |
| Shared battle status: 8 (history capacity exceeded) | 9 |
| Shared battle status: 64 | 6 |
| Cover DEF composition requires a connected BODY/PART modifier or shot-group product battle | 6 |
| Enemy magazines require a checked plain, modifier or actual-shot group BODY/ADD product prefix | 1 |
| Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry | 4 |
| Cover DEF requires complete independent bases and receipt bank | 1 |

Before Part B: 29.182 GiB free; 2 GiB additional peak budget and 20 GiB reserve passed both shutil.disk_usage and storage-check. No raw captures retained.

Before Part D: 28.114 GiB free; 2 GiB additional peak budget and 20 GiB reserve passed both shutil.disk_usage and storage-check. No raw captures retained.

## Part C: features, fitting and selection

Target is natural log damage. M0 is the unchanged unfitted sum potential, mapped through log for RMSE; it has no fitted damage calibration. M1 uses 206 membership indicators and an unpenalized intercept. M2 adds `(character, within-stage rank)` indicators: scan the ordered tuple left to right, count preceding members whose literal burst-stage label equals this character’s label, and use ranks 0–4. A is its own stage group; this feature does not expand A into stages 1/2/3. M1/M2 ridge penalty is λ × sum(weights²); loss is sum squared errors. Choose λ from {0.1,1,10,100} by five interleaved folds of the seed-45 shuffled training rows, minimizing pooled validation log MSE. M1/M2 use matrix-free centered conjugate gradients with relative squared residual <1e-14 or 250 steps. M4 uses centered normal equations and Cholesky; sufficient statistics are collected separately for each training fold.
M3 is an unordered membership factorization machine: intercept + sum character biases + sum pairwise factor dot products. Seed 47 initializes factors and shuffles SGD. 35 epochs, rate 0.015/(1+0.06×epoch), clipped residual ±5. Choose rank {4,8,16} and regularization {0.001,0.01,0.1} on the first 20% of training (fit the remaining 80%), minimizing log MSE, then refit all training. Intercept is the training mean; regularization applies to active biases/factors at each update.
M4 contains no character IDs: counts of burst-stage, element, weapon, class and manufacturer, plus sums of numeric base stats derived from the S1 profile by existing static stat calculation. Aggregate inputs are burst_stage=1, burst_stage=2, burst_stage=3, burst_stage=A, element_code=수냉, element_code=작열, element_code=전격, element_code=철갑, element_code=풍압, weapon_type=AR, weapon_type=MG, weapon_type=RL, weapon_type=SG, weapon_type=SMG, weapon_type=SR, class=방어형, class=지원형, class=화력형, manufacturer=미실리스, manufacturer=어브노말, manufacturer=엘리시온, manufacturer=테트라, manufacturer=필그림, atk, def, hp. Numeric fields are divided by the maximum absolute per-character value in the profile (no labels); categorical fields are unscaled. Include all upper-triangle products of these squad sums/counts, including squares. Ridge selection is identical to M1. This feature map can score unseen identities when their attributes are supplied; unseen category values require an expanded schema/refit.
All fitting uses training only; holdout selects the search model by top-100 recall at K=5%, with model order breaking ties. All top-K sizes are ceil(fraction×evaluated n), ties use stable row ID. Spearman uses average ranks; Kendall is tie-corrected tau-b. Learning curves use training prefixes and the full-training-selected hyperparameters; they measure data volume with those fixed settings.

| Model | Fit + selection wall seconds | Selected settings |
|---|---:|---|
| M1 | 2.974 | {'lam': 0.1} |
| M2 | 17.551 | {'lam': 0.1} |
| M4 | 31.268 | {'lam': 0.1} |
| M3 | 76.977 | {'k': 16, 'reg': 0.01, 'epochs': 35} |

| Model | Set | n | Spearman | Kendall tau-b | log RMSE |
|---|---|---:|---:|---:|---:|
| M0 | holdout | 1956 | 0.063097 | 0.042752 | 2.433964 |
| M0 | S1-external | 2406 | 0.079420 | 0.054301 | 2.429995 |
| M0 | S1-A | 160 | -0.082389 | -0.043396 | 2.361105 |
| M0 | S1-B | 1950 | 0.074978 | 0.051053 | 2.451643 |
| M0 | S1-C | 296 | -0.006446 | -0.002016 | 2.321011 |
| M1 | holdout | 1956 | 0.902649 | 0.730077 | 0.185604 |
| M1 | S1-external | 2406 | 0.877667 | 0.702886 | 0.220042 |
| M1 | S1-A | 160 | 0.890959 | 0.723742 | 0.270340 |
| M1 | S1-B | 1950 | 0.909601 | 0.738851 | 0.180435 |
| M1 | S1-C | 296 | 0.751339 | 0.551031 | 0.373604 |
| M2 | holdout | 1956 | 0.949117 | 0.805470 | 0.139657 |
| M2 | S1-external | 2406 | 0.944152 | 0.798473 | 0.152699 |
| M2 | S1-A | 160 | 0.948957 | 0.812107 | 0.221253 |
| M2 | S1-B | 1950 | 0.951198 | 0.809375 | 0.132997 |
| M2 | S1-C | 296 | 0.880292 | 0.701878 | 0.215735 |
| M3 | holdout | 1956 | 0.905772 | 0.736302 | 0.180087 |
| M3 | S1-external | 2406 | 0.877523 | 0.705724 | 0.220381 |
| M3 | S1-A | 160 | 0.897217 | 0.738208 | 0.259355 |
| M3 | S1-B | 1950 | 0.910252 | 0.743135 | 0.178651 |
| M3 | S1-C | 296 | 0.743659 | 0.544755 | 0.384916 |
| M4 | holdout | 1956 | 0.721595 | 0.529526 | 0.289003 |
| M4 | S1-external | 2406 | 0.707195 | 0.515783 | 0.308338 |
| M4 | S1-A | 160 | 0.661848 | 0.477516 | 0.433564 |
| M4 | S1-B | 1950 | 0.715113 | 0.521789 | 0.291786 |
| M4 | S1-C | 296 | 0.682368 | 0.495236 | 0.332101 |

### Top-N recall

| Model / set | True top-N | K=1% | K=5% | K=10% | K=20% |
|---|---:|---:|---:|---:|---:|
| M0 / holdout | 20 | 0.00% | 0.00% | 0.00% | 25.00% |
| M0 / holdout | 100 | 1.00% | 7.00% | 13.00% | 30.00% |
| M0 / S1-external | 20 | 20.00% | 20.00% | 20.00% | 25.00% |
| M0 / S1-external | 100 | 5.00% | 5.00% | 8.00% | 19.00% |
| M0 / S1-A | 20 | 0.00% | 15.00% | 20.00% | 20.00% |
| M0 / S1-A | 100 | 2.00% | 6.00% | 13.00% | 22.00% |
| M0 / S1-B | 20 | 5.00% | 10.00% | 15.00% | 20.00% |
| M0 / S1-B | 100 | 2.00% | 5.00% | 10.00% | 23.00% |
| M0 / S1-C | 20 | 0.00% | 10.00% | 15.00% | 20.00% |
| M0 / S1-C | 100 | 3.00% | 8.00% | 12.00% | 21.00% |
| M1 / holdout | 20 | 45.00% | 90.00% | 100.00% | 100.00% |
| M1 / holdout | 100 | 17.00% | 58.00% | 86.00% | 99.00% |
| M1 / S1-external | 20 | 55.00% | 75.00% | 90.00% | 100.00% |
| M1 / S1-external | 100 | 17.00% | 60.00% | 84.00% | 98.00% |
| M1 / S1-A | 20 | 10.00% | 40.00% | 70.00% | 80.00% |
| M1 / S1-A | 100 | 2.00% | 8.00% | 16.00% | 32.00% |
| M1 / S1-B | 20 | 50.00% | 85.00% | 95.00% | 95.00% |
| M1 / S1-B | 100 | 16.00% | 63.00% | 87.00% | 96.00% |
| M1 / S1-C | 20 | 0.00% | 15.00% | 40.00% | 85.00% |
| M1 / S1-C | 100 | 3.00% | 12.00% | 22.00% | 42.00% |
| M2 / holdout | 20 | 55.00% | 95.00% | 100.00% | 100.00% |
| M2 / holdout | 100 | 19.00% | 73.00% | 93.00% | 98.00% |
| M2 / S1-external | 20 | 60.00% | 80.00% | 95.00% | 100.00% |
| M2 / S1-external | 100 | 23.00% | 73.00% | 93.00% | 100.00% |
| M2 / S1-A | 20 | 10.00% | 40.00% | 65.00% | 95.00% |
| M2 / S1-A | 100 | 2.00% | 8.00% | 16.00% | 32.00% |
| M2 / S1-B | 20 | 65.00% | 95.00% | 100.00% | 100.00% |
| M2 / S1-B | 100 | 19.00% | 73.00% | 93.00% | 99.00% |
| M2 / S1-C | 20 | 10.00% | 60.00% | 90.00% | 100.00% |
| M2 / S1-C | 100 | 3.00% | 15.00% | 29.00% | 55.00% |
| M3 / holdout | 20 | 40.00% | 100.00% | 100.00% | 100.00% |
| M3 / holdout | 100 | 17.00% | 64.00% | 87.00% | 98.00% |
| M3 / S1-external | 20 | 60.00% | 80.00% | 90.00% | 100.00% |
| M3 / S1-external | 100 | 17.00% | 60.00% | 84.00% | 98.00% |
| M3 / S1-A | 20 | 10.00% | 40.00% | 65.00% | 80.00% |
| M3 / S1-A | 100 | 2.00% | 8.00% | 16.00% | 32.00% |
| M3 / S1-B | 20 | 60.00% | 85.00% | 95.00% | 95.00% |
| M3 / S1-B | 100 | 17.00% | 63.00% | 87.00% | 96.00% |
| M3 / S1-C | 20 | 0.00% | 15.00% | 45.00% | 75.00% |
| M3 / S1-C | 100 | 3.00% | 12.00% | 23.00% | 41.00% |
| M4 / holdout | 20 | 15.00% | 70.00% | 80.00% | 85.00% |
| M4 / holdout | 100 | 11.00% | 42.00% | 62.00% | 77.00% |
| M4 / S1-external | 20 | 50.00% | 60.00% | 65.00% | 90.00% |
| M4 / S1-external | 100 | 17.00% | 38.00% | 53.00% | 73.00% |
| M4 / S1-A | 20 | 10.00% | 25.00% | 35.00% | 45.00% |
| M4 / S1-A | 100 | 2.00% | 8.00% | 16.00% | 30.00% |
| M4 / S1-B | 20 | 40.00% | 60.00% | 80.00% | 90.00% |
| M4 / S1-B | 100 | 14.00% | 40.00% | 59.00% | 76.00% |
| M4 / S1-C | 20 | 0.00% | 30.00% | 50.00% | 85.00% |
| M4 / S1-C | 100 | 1.00% | 13.00% | 23.00% | 42.00% |

### Learning curves

| Model | Training n | Spearman | Kendall tau-b | log RMSE |
|---|---:|---:|---:|---:|
| M1 | 1000 | 0.872754 | 0.688950 | 0.204485 |
| M3 | 1000 | 0.869453 | 0.685301 | 0.206235 |
| M1 | 2500 | 0.893444 | 0.718661 | 0.190684 |
| M3 | 2500 | 0.890071 | 0.714531 | 0.193156 |
| M1 | 5000 | 0.899907 | 0.726048 | 0.187003 |
| M3 | 5000 | 0.899201 | 0.725165 | 0.187406 |
| M1 | 10000 | 0.902649 | 0.730077 | 0.185604 |
| M3 | 10000 | 0.905772 | 0.736302 | 0.180087 |

Learning-curve recall

| Model / set | True top-N | K=1% | K=5% | K=10% | K=20% |
|---|---:|---:|---:|---:|---:|
| M1 / 1000 | 20 | 40.00% | 90.00% | 95.00% | 100.00% |
| M1 / 1000 | 100 | 17.00% | 57.00% | 84.00% | 98.00% |
| M3 / 1000 | 20 | 40.00% | 95.00% | 95.00% | 100.00% |
| M3 / 1000 | 100 | 18.00% | 57.00% | 84.00% | 98.00% |
| M1 / 2500 | 20 | 40.00% | 90.00% | 100.00% | 100.00% |
| M1 / 2500 | 100 | 16.00% | 58.00% | 89.00% | 99.00% |
| M3 / 2500 | 20 | 40.00% | 90.00% | 100.00% | 100.00% |
| M3 / 2500 | 100 | 17.00% | 58.00% | 88.00% | 99.00% |
| M1 / 5000 | 20 | 40.00% | 90.00% | 100.00% | 100.00% |
| M1 / 5000 | 100 | 16.00% | 55.00% | 87.00% | 99.00% |
| M3 / 5000 | 20 | 30.00% | 95.00% | 100.00% | 100.00% |
| M3 / 5000 | 100 | 16.00% | 58.00% | 86.00% | 98.00% |
| M1 / 10000 | 20 | 45.00% | 90.00% | 100.00% | 100.00% |
| M1 / 10000 | 100 | 17.00% | 58.00% | 86.00% | 99.00% |
| M3 / 10000 | 20 | 40.00% | 100.00% | 100.00% | 100.00% |
| M3 / 10000 | 100 | 17.00% | 64.00% | 87.00% | 98.00% |

## Part D: search test

Selected **M2** by held-out top-100 recall at K=5%. Scored 1,000,000 fresh ordered covered squads, excluding all evaluated tuples and exact duplicates.
Scoring only: 6.292 s/million; generation + coverage + duplicate checks + scoring + top-300 heap: 13.619 s.
Top-300 native outcomes: {'generated': 300, 'native_ok': 300, 'backends': {'native_detail': 300}, 'failed_by_reason': {}}

| Detailed damage statistic | Search native successes | Random 12,000 + S1 B/C native successes |
|---|---:|---:|
| n | 300.000 | 14,202.000 |
| max | 5,088,218,087.000 | 4,675,146,360.000 |
| top10_mean | 4,838,191,194.900 | 3,463,241,574.900 |
| median | 3,042,113,789.000 | 695,115,365.000 |
| p99 | 4,962,266,517.000 | 2,067,416,584.000 |
| p90 | 4,040,281,490.000 | 1,255,092,813.000 |

Search squads beating random dataset best / 99th / 90th percentile: **8 / 287 / 300**. Percentiles use nearest rank; strict greater-than comparisons.
Top-end Spearman on 300 successful selected squads: **0.267738** (Kendall 0.180424).

Linear extrapolation from scoring-only time to 2.9 billion sets: 5.069 hours; exact C(206,5)=2,943,861,746: 5.146 hours. This excludes enumeration, constraints, top-K retention and native evaluation. Ordered priority variants multiply the work; an unordered set has up to 120 orders. This is a time projection, not a run.
For additive M1, remaining-character weight maxima give admissible branch-and-bound bounds; M2 also needs bounds over possible stage ranks: each remaining character can use its membership weight plus its largest feasible rank weight as an upper bound. For a fixed membership set, maximizing the model over within-stage orders is a small assignment problem in each stage group. For M3, precompute pairwise dot products and use remaining bias maxima plus upper bounds on chosen-to-remaining and remaining-to-remaining pair contributions. M4 admits interval bounds on aggregate attributes and their products. Such bounds can be loose; no pruning performance or global optimum is established here.

## Reproduction, commands and wall times

Run from this worktree with Python 3.12; no packages are installed. `models` retrains and recomputes Part C from saved JSONL without native evaluation. `search-stats` recomputes Part D statistics from saved search JSONL without evaluation (original timing metadata comes from scratch or the saved summary). `report` assembles the saved results. Timing fields naturally differ on recomputation; predictions, selections, split IDs and numerical metrics are deterministic.

```sh
python3.12 research/team-search/measure_s9.py --help
python3.12 research/team-search/measure_s9.py dataset
python3.12 research/team-search/measure_s9.py models
python3.12 research/team-search/measure_s9.py search
python3.12 research/team-search/measure_s9.py search-stats
python3.12 research/team-search/measure_s9.py report
```

Part B summed batch wall: 1903.633 s (all batches have 32 rows). Part C total wall: 159.884 s. Per-model wall above includes selection and final refit; learning-curve timings are in summary JSON.
Exact session commands and measured command wall times are recorded in `$S/s9/commands.jsonl`.

## Open issues

Single profile/scenario, unverified native rankings, finite random sample and native failure exclusions limit generalization. Holdout is smaller than 2,000 because failed native rows cannot be ranked. No uncertainty intervals or cross-scenario tests were requested. Search-model selection consumes the holdout; S1 external is untouched by selection. High average correlation does not establish safe pruning; use the measured top-tail recall and independent top-300 detailed test. Models M1–M3 use identities and cannot extrapolate to unseen characters; M4 can use supplied known-schema attributes, but no leave-character-out experiment was run. This S9 run made no product changes, CPU reference runs, GPU work, installs, commit or push. Unrelated edits appeared elsewhere in the worktree during collection and were left untouched.

## Assessment

The selected model retains 73.0% of the held-out detailed top-100 in a 5% shortlist. This does not meet the design memo’s 99% recall goal for safe aggressive pruning.
The guided search maximum is +8.8% relative to the best random-data squad. This measures candidate discovery in this scenario; it does not establish global coverage or optimality.
At K=20%, M2 retains 98.0% of the held-out top-100 and 100.0% externally. A wider shortlist is promising, but held-out recall still falls short of 99%.

### Actual recorded commands

| Command | Wall seconds |
|---|---:|
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -c 'import sys;sys.path.insert(0,'"'"'research/team-search'"'"');import measure_s9 as s;s.dataset()'` | 1906.263 |
| `/opt/homebrew/opt/python@3.12/bin/python3.12 research/team-search/measure_s9.py models` | 54.512 |
| `/opt/homebrew/opt/python@3.12/bin/python3.12 research/team-search/measure_s9.py models` | 160.018 |
| `/opt/homebrew/opt/python@3.12/bin/python3.12 research/team-search/measure_s9.py search` | 135.738 |
| `/opt/homebrew/opt/python@3.12/bin/python3.12 research/team-search/measure_s9.py search-stats` | 0.111 |
| `/opt/homebrew/opt/python@3.12/bin/python3.12 research/team-search/measure_s9.py report` | 0.081 |
| `/opt/homebrew/opt/python@3.12/bin/python3.12 /Users/edo/Documents/ChatGPT/nikke_tools/.portable-recovery/proofs/claude-product-standard-phase0-v1-20261102/team-search-v1/s9/validate_s9.py` | 0.273 |
| `/opt/homebrew/opt/python@3.12/bin/python3.12 /Users/edo/Documents/ChatGPT/nikke_tools/.portable-recovery/proofs/claude-product-standard-phase0-v1-20261102/team-search-v1/s9/validate_s9.py` | 0.307 |
| `/opt/homebrew/opt/python@3.12/bin/python3.12 research/team-search/measure_s9.py report` | 0.082 |

The initial dataset command wall is approximated from log creation to final batch write; all CLI command walls use perf_counter. The separate analytical/pilot checks did not contribute training data.
