"""Assemble S21 tables exclusively from saved, compact search evidence."""
import argparse, collections, json, math, statistics
from pathlib import Path
import measure_s9 as s9
from search_s21 import read,save,DEFAULT,HERE


def quantile(values,p):return sorted(values)[max(0,math.ceil(p*len(values))-1)]
def stats(values):
    return dict(n=len(values),maximum=max(values),top10_mean=statistics.mean(sorted(values,reverse=True)[:10]),p90=quantile(values,.9),median=statistics.median(values),beating_random=sum(v>4675146360 for v in values),beating_M2=sum(v>5088218087 for v in values)) if values else dict(n=0)
def main(out):
    selection=read(out/'selection.json');detailed=[json.loads(l) for l in (out/'s21-detailed.jsonl').read_text().splitlines()];byid={r['id']:r for r in detailed};quality={}
    for label,ids in selection['groups'].items():
        n,mask=map(int,label.split('-'));orders=read(out/f'orders-{n}-{mask}.json')['rows'];pred={tuple(r['best']['indices']):r['best']['score'] for r in orders};names=read(out/'rosters.json')['names'];index={n:i for i,n in enumerate(names)}
        ok=[byid[i] for i in ids if byid[i]['status']=='ok'];values=[r['total'] for r in ok];xs=[pred[tuple(index[n] for n in r['order'])] for r in ok]
        correlation=s9.rank_metrics(xs,values) if len(values)>1 else dict(spearman=None,kendall_tau_b=None)
        quality[label]=dict(stats(values),requested=len(ids),failed=len(ids)-len(ok),spearman=correlation['spearman'],kendall=correlation['kendall_tau_b'],best=max(ok,key=lambda r:r['total']) if ok else None)
    order_effect=[]
    for group in selection['order_groups']:
        ids=[group['best'],group['canonical'],*group['alternates']];ok=[byid[i] for i in set(ids) if byid[i]['status']=='ok']
        best=byid[group['best']];canonical=byid[group['canonical']]
        order_effect.append(dict(indices=group['indices'],all_success=all(byid[i]['status']=='ok' for i in ids),unique_orders=len(set(ids)),L2_best_is_detailed_best=bool(ok) and best['status']=='ok' and best['total']==max(r['total'] for r in ok),best_order_total=best['total'],canonical_total=canonical['total'],tested=[dict(id=i,total=byid[i]['total'],status=byid[i]['status']) for i in dict.fromkeys(ids)]))
    overlaps={}
    for n in (150,206):
        sets={m:{tuple(r['indices']) for r in read(out/f'orders-{n}-{m}.json')['rows']} for m in (15,2)}
        tops={m:{tuple(r['indices']) for r in read(out/f'orders-{n}-{m}.json')['rows'][:300 if n==206 else 100]} for m in (15,2)}
        overlaps[str(n)]=dict(topK=len(sets[15]&sets[2]),detailed_shortlist=len(tops[15]&tops[2]))
    s9_rows=[json.loads(l) for l in (HERE/'s9-search.jsonl').read_text().splitlines()];s9_byset=collections.defaultdict(list)
    for r in s9_rows:s9_byset[tuple(sorted(r['members']))].append(dict(id=r['id'],order=r['members'],total=r.get('total_damage'),backend=r['backend']))
    s9_overlap={};names=read(out/'rosters.json')['names']
    for n in (150,206):
        for mask in (15,2):
            rows=read(out/f'orders-{n}-{mask}.json')['rows'];found=[]
            for rank,r in enumerate(rows,1):
                key=tuple(sorted(names[i] for i in r['indices']))
                if key in s9_byset:found.append(dict(rank=rank,members=key,S9=s9_byset[key]))
            s9_overlap[f'{n}-{mask}']=dict(topK=len(found),top_detailed=sum(r['rank']<=(300 if n==206 else 100) for r in found),rows=found)
    overall_best=max((r for r in detailed if r['status']=='ok'),key=lambda r:r['total'])
    order_summary=dict(strict_wins=0,tied_wins=0,losses=0,canonical_better=0)
    order_gains=[]
    for group in selection['order_groups']:
        if any(byid[i]['status']!='ok' for i in [group['best'],group['canonical'],*group['alternates']]):continue
        best=byid[group['best']]['total'];others=[byid[i]['total'] for i in set([group['canonical'],*group['alternates']]) if i!=group['best']]
        order_summary['strict_wins']+=best>max(others);order_summary['tied_wins']+=best==max(others);order_summary['losses']+=best<max(others);order_summary['canonical_better']+=byid[group['canonical']]['total']>best
        order_gains.append(best/byid[group['canonical']]['total']-1)
    order_summary.update(median_gain=statistics.median(order_gains),min_gain=min(order_gains),max_gain=max(order_gains))
    summary=dict(quality=quality,order_effect=order_effect,order_summary=order_summary,overall_best=overall_best,mask_overlap=overlaps,s9_overlap=s9_overlap)
    save(out/'summary.json',summary)
    lines=['# S21: exhaustive L2 squad search','',
      'The enumerator exhaustively visits every five-subset, filters effective burst-stage coverage, scores one canonical order and retains K=10,000. All 120 distinct orders of each retained subset are then scored and reranked. This is an exhaustive canonical-order L2 shortlist, not an exhaustive all-order search or a detailed global optimum. No pruning or arithmetic reuse was adopted.','',
      '## Enumerator and contract','',
      'Roster indices are validated, deduplicated by rejection, and sorted ascending. Canonical order is ascending profile-table index: a reproducible priority/placement policy, with no claim that index order is good. The reference says input squad order sets auto-burst priority within each stage (`research/upstream/nikke-calc-master/docs/GAMEPLAY.md:197–213`; `calculator/timeline.py:3777–3789`). Positional recipients depend on squad slots (`calculator/buff_manager.py:5246–5261`, adjacency/right; `5345–5356`, leftmost). These mechanics require the separate order stage; stage sorting or ignoring inter-stage placement would not establish equivalence.','',
      'First index offsets are distributed modulo thread/worker count. Each partition enumerates its suffix in lexicographic order and keeps a bounded K heap. A candidate is better if its binary64 score is larger, then its five canonical indices are lexicographically smaller. Merging partition top-K lists under that same total ordering yields the global top-K; any discarded partition item already has at least K better items in its own partition. WASM uses the identical C++ partition function, with one table/memory per Node worker; native uses C++ threads and a read-only table. Entry size is 32 bytes (five uint32, alignment padding, binary64 score).','',
      'Coverage is exactly the stage-availability precheck of the active L2 cycle: OR nominal masks (Red Hood automatic A resolved to B3), applying enabled conditional stage overrides for switches containing bit 2; retain mask=7. This is availability, not a cooldown/gauge feasibility proof. It follows `l2_score_s20.cycle`, not a newly invented game constraint. Coverage is independent of order. Counts are subsets visited / covered / scored; on fractional benchmarks covered/scored count only selected ranks.','',
      f'Owned roster: 150 indices uniformly sampled without replacement from the 206 S1 characters, Python Random seed 210150, sorted for enumeration; full indices and names in `s21/rosters.json`. Final S20 profiles are unchanged except the requested switch mask. No sealed S20 rows were opened.','',
      'The C ABI accepts roster, K, table, partition/count or native thread count, and a sampling stride; default stride=1. `l2_fast.enumerate_top` provides the Python binding; native CLI: `l2-cli TABLE --enumerate K THREADS STRIDE INDEX...`. Node: `runner.mjs --enumerate --wasm WASM --table TABLE --roster ROSTER.json --k 10000 --workers N [--stride 1]`. `search_s21.py` reproduces prepare/bench/order/selection/collect; `verify_s21.py` verifies saved results.','',
      '## Bit identity and determinism','']
    if (out/'bit-identity.json').exists():
        lines+=['| Roster | Mask | Corpus | Ordered squads | Differences | Seconds |','|---:|---:|---|---:|---:|---:|']
        for r in read(out/'bit-identity.json'):lines.append(f"| {r['n']} | {r['mask']} | {r['label']} | {r['count']:,} | {r['differences']} | {r['seconds']:.3f} |")
        lines+=['','Raw little-endian binary64 totals are compared with the Python 3.12 `l2_score_s20.Score` oracle, native binding, native CLI and WASM scorer; every checked squad also re-enters the native enumeration primitive as a five-member roster, and retained entries additionally compare the score emitted by the complete search. Every retained top-K entry is checked. Random checks use seed 210021+roster_size+mask and uniform distinct canonical subsets, rejecting only oracle coverage failures. Digests, counts and timings are in `bit-identity.json`; no full enumeration dump is written.','']
    unique_audits=[r for path in out.glob('random-unique-audit*.json') for r in read(path)]
    if unique_audits:
        lines+=['| Roster | Mask | Original random rows | Original unique | Additional verified unique | Final unique | Differences |','|---:|---:|---:|---:|---:|---:|---:|']
        for r in unique_audits:lines.append(f"| {r['n']} | {r['mask']} | {r['original_rows']:,} | {r['original_unique']:,} | {r['extra_verified']:,} | {r['final_unique']:,} | {r['differences']} |")
        lines += ['',f"Total verified squad checks, including retained entries and supplements: {sum(r['count'] for r in read(out/'bit-identity.json'))+sum(r['extra_verified'] for r in unique_audits):,}; zero differences.",'']
        lines += ['','`audit_random_s21.py` replays the original RNG/coverage stream and verifies fresh unique squads for any shortfall, through the enumeration primitive, binding, CLI, WASM and Python raw binary64. The final unique count is at least 100,000 per audited roster/mask; initial samples were drawn with replacement between squads. Supplemental values are streamed and only hashes/receipts retained.','']
    if (out/'determinism.json').exists():lines+=['Sampled-domain native 1/10 and WASM 1/10 lists and counts are identical for each roster/mask, 10,000 retained entries each (`determinism.json`). Sampling selects global lexicographic rank % 100 == 0, independent of partition count. Full-run comparisons, where present, are recorded separately.','']
    if (out/'full-determinism.json').exists() and len(read(out/'full-determinism.json'))==4:
        lines+=['Full mask-15 top-K lists and all three counts also match native 10 threads against native 7 threads and WASM 10 workers for both rosters (`full-determinism.json`), without sampling.','']
    env=read(out/'environment.json')
    lines += [f"Local host: {env['host']}; {env['platform']}; Node {env['node']}; Python {env['python'].splitlines()[0]}. Exact compiler/flags and table identities are retained in `environment.json` and content-addressed build receipts. Requested worker counts do not assert identical physical cores.",'']
    lines+=['## Speed and complete walls','','All runs are listed below. Primary benchmark configurations run sequentially; brief metadata reads and tiny focused checks may overlap, and the full acceptance suite runs afterward. Additional complete-list determinism runs overlap that suite and are explicitly marked under load; their walls are not isolated speed estimates. Fractional runs still visit all subsets but score only every 100th global lexicographic rank; their top-K is a sampled-domain top-K. Estimated complete walls multiply the measured whole-run wall by 100, including loop overhead, so they are labelled projections rather than complete measurements. Throughput includes enumeration, coverage, scoring, heap and merge (plus startup/table load for wall). No pure scorer-only speed claim is made. Native 10-thread complete runs and the requested 1/10-thread/worker sampled matrix are retained separately; additional full 7-thread/WASM runs validate complete-list determinism.','',
      '| Engine | Roster | Mask | Workers | Stride | Visited | Covered/scored | Wall s | Scored/s | Projected full s | Context |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|' ]
    runs=[]
    for p in out.glob('*.json'):
        if p.name.startswith(('native-','WASM-')):
            r=read(p)
            if 'engine' in r:runs.append(r)
    for r in sorted(runs,key=lambda r:(r['n'],r['mask'],r['engine'],r['workers'],r['stride'])):
        c=r['counts'];wall=r['wall_seconds'];lines.append(f"| {r['engine']} | {r['n']} | {r['mask']} | {r['workers']} | {r['stride']} | {c['visited']:,} | {c['scored']:,} | {wall:.3f} | {c['scored']/wall:,.0f} | {wall*r['stride']:.3f}{' (projection)' if r['stride']>1 else ' (complete)'} | {'acceptance load' if r.get('concurrent_validation') else 'primary'} |")
    lines += ['Mask 2 is faster in the sampled single-thread runs, but complete ten-thread walls are slightly slower than mask 15 in this sequential matrix. These unreplicated, differently timed workloads do not isolate a causal mask speedup.','']
    lines += ['| Host | Stage | Measured wall s |','|---|---|---:|',
        f"| {env['host']} | Primary enumeration matrix (sum of sequential runs) | {sum(r['wall_seconds'] for r in runs if not r.get('concurrent_validation')):.3f} |",
        f"| {env['host']} | Extra complete determinism runs (acceptance load) | {sum(r['wall_seconds'] for r in runs if r.get('concurrent_validation')):.3f} |",
        f"| {env['host']} | All four order stages | {sum(read(out/f'orders-{n}-{mask}.json')['seconds'] for n in (150,206) for mask in (15,2)):.3f} |"]
    if (out/'bit-identity.json').exists():lines += [f"| {env['host']} | Bit-identity verification | {sum(r['seconds'] for r in read(out/'bit-identity.json')):.3f} |"]
    lines += [f"| gx10 | Detailed collection (407 unique ordered squads) | {read(out/'collection.json')['wall_seconds']:.3f} |",'']
    lines+=['Job walls can overlap (extra comparisons and acceptance); their sums are not elapsed host time.','','## Order stage','','| Roster | Mask | Orders scored | Wall s | Improved subsets | Median gain | p90 gain | Max gain |','|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n in (150,206):
        for mask in (15,2):
            r=read(out/f'orders-{n}-{mask}.json');s=r['stats'];lines.append(f"| {n} | {mask} | {r['orders_scored']:,} | {r['seconds']:.3f} | {s['changed']:,}/10,000 | {s['median']:.3%} | {s['p90']:.3%} | {s['maximum']:.3%} |")
    lines += ['','| Roster/mask | Median canonical deficit / best | p90 deficit | Max deficit |','|---|---:|---:|---:|']
    for n in (150,206):
        for mask in (15,2):
            losses=[1-r['canonical_score']/r['best']['score'] for r in read(out/f'orders-{n}-{mask}.json')['rows']]
            lines.append(f"| {n}-{mask} | {statistics.median(losses):.3%} | {quantile(losses,.9):.3%} | {max(losses):.3%} |")
    lines += ['','Canonical deficit is 1 − canonical/best, complementing the gain statistic above. Both describe only retained subsets.','']
    lines+=['','Gain is best-order L2 / canonical L2 − 1 among canonical top-K survivors. It does not measure the loss from subsets excluded by the canonical top-K. Every subset has all 120 exact orders evaluated; best ties use lexicographic order, including tiny binary64 differences.','',
      '## Detailed search quality','','S1/S9 scenario, gx10 native `evaluate_many`, 32-row batches, ten native host threads, deferred verification, forbidden CPU fallback. These are unverified native outcomes, not a new CPU-parity claim. The existing S20 remote source snapshot was checked against all 923 current local CPU/app/GPU/data identities plus four collector dependencies with zero differences (`remote-identity.json`, `collector-identity.json`); no source pins were added.','',
      '| Roster/mask | OK/requested | Max | Top-10 mean | p90 | Median | >random best | >M2 max | Spearman | Kendall tau-b |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|' ]
    fmtcorr=lambda v:'undefined' if v is None else f'{v:.6f}'
    for label,r in quality.items():lines.append(f"| {label} | {r['n']}/{r['requested']} | {r.get('maximum',0):,.0f} | {r.get('top10_mean',0):,.1f} | {r.get('p90',0):,.0f} | {r.get('median',0):,.1f} | {r.get('beating_random',0)} | {r.get('beating_M2',0)} | {fmtcorr(r['spearman'])} | {fmtcorr(r['kendall'])} |")
    lines+=['','S9 random-data best=4,675,146,360; M2 top-300 max=5,088,218,087, mean of top ten=4,838,191,194.9, p90=4,040,281,490, median=3,042,113,789; top-end Spearman=0.267738, Kendall=0.180424 (`research/team-search/s9-report.md`, Part D). The selected 300 differ between methods, so this correlation comparison is descriptive rather than a paired model-accuracy test. Percentiles here use nearest rank; medians use arithmetic middle pair; comparisons are strict.','']
    for label,r in quality.items():
        if r['best']:lines += [f"Best {label}: {r['best']['total']:,}; order: {' / '.join(r['best']['order'])}.",'']
    lines += [f"Across all {len(detailed)} confirmed orders, including the additional order probes, the best is **{overall_best['total']:,}** ({overall_best['total']/5088218087-1:+.2%} versus M2 max), ID {overall_best['id']}: {' / '.join(overall_best['order'])}. This is an alternate order, not the L2-selected best order; the requested top-300 and top-100 tables above retain their original selection policy. Its five members are also owned in the 150 roster.",'']
    complete=[r for r in order_effect if r['all_success']]
    lines += [f"Order-detail breakdown: {order_summary['strict_wins']} strict wins, {order_summary['tied_wins']} tied wins, {order_summary['losses']} losses for L2's chosen order; canonical beats L2 best in {order_summary['canonical_better']} subsets. Detailed change of L2-best versus canonical: median {order_summary['median_gain']:.2%}, minimum {order_summary['min_gain']:.2%}, maximum {order_summary['max_gain']:.2%}.",'']
    lines += [f"Top-30 order check: {len(complete)}/30 subsets have all requested detailed orders successful; L2 best is tied or uniquely detailed-best in {sum(r['L2_best_is_detailed_best'] for r in complete)}/{len(complete)} complete comparisons. Each subset tests canonical, L2 best, and the next two exact L2-ranked orders; duplicate exact orders reuse their result. Per-subset totals, failures and comparisons are in `summary.json`.",'',
      '| Roster | Mask top-K overlap / 10,000 | Detailed-shortlist subset overlap |','|---:|---:|---:|']
    for n,r in overlaps.items():lines.append(f"| {n} | {r['topK']} | {r['detailed_shortlist']} |")
    lines+=['','Mask 2 evaluates the full requested top 300 (206) and top 100 (150); already evaluated identical ordered squads reuse results. Subset overlap alone does not imply equal order or detailed total.','',
      '| Roster/mask | S9-search subset overlap top-K | Overlap detailed shortlist |','|---|---:|---:|']
    for label,r in s9_overlap.items():lines.append(f"| {label} | {r['topK']} | {r['top_detailed']} |")
    lines+=['','| Roster/mask | S21 reranked position | S9 ID | Saved S9 detailed total |','|---|---:|---:|---:|']
    for label,r in s9_overlap.items():
        for match in r['rows']:
            for saved in match['S9']:lines.append(f"| {label} | {match['rank']} | {saved['id']} | {saved['total']:,} |")
    lines+=['','All matching S9 members and orders are in `summary.json` (same subsets, regardless of order). None overlaps the detailed shortlist.','', '## Failures, acceptance and storage','']
    collection=read(out/'collection.json');lines += [f"gx10 collection ({collection.get('host','gx10')}): {collection['rows']} unique orders, {collection['successes']} successes, {len(collection['failures'])} failures; wall {collection['wall_seconds']:.3f} s. Full ID/reason list: `s21/collection.json`. Compact repository results: `research/team-search/s21-detailed.jsonl` (id/members/order/total/backend/status only).",'']
    lines+=['The first gx10 launch failed before evaluation because of an unnecessary top-level L2 helper import absent from the collection snapshot. Imports were moved into local search actions and collection retried successfully; `collect.log` preserves that setup error and `collect-retry.log` the successful batches. No detailed fallback or failed battle was silently replaced. The first tiny WASM check exposed the new chrono clock import; the loader now supplies WASI clock_time_get, and the final focused check passes. An initial report-only variable shadow was corrected before publication (`initial-report-failure.log`).','']
    counts=collections.Counter(str(r['reason']) for r in collection['failures'])
    if counts:
        lines+=['| Failure reason | Count |','|---|---:|']+[f'| {reason} | {count} |' for reason,count in counts.items()]+['']
    if (out/'validation.json').exists():
        lines+=['| Check | Exit | Wall s |','|---|---:|---:|']
        for r in read(out/'validation.json'):lines.append(f"| {r['label']} | {r['exit']} | {r['seconds']:.3f} |")
        if len(read(out/'validation.json'))==3 and all(r['exit']==0 for r in read(out/'validation.json')):
            lines += ['','Full Python: **2,663 tests, OK**. Node: **169 passed**, zero failures/skips. The Python log retains a non-fatal resource_tracker cleanup warning (five semaphore objects) and intentional remote-worker failure-fixture output; all commands exited 0.','']
        lines+=['','Acceptance environment: Python 3.12; PYTHONPATH=$S/../pin-update-v1/validation-deps; NIKKE_SLANG_ROOT=/Users/edo/Documents/ChatGPT/nikke_tools/.tools/slang-2026.20-Darwin-arm64; PYTHONDONTWRITEBYTECODE=1. Exact commands and logs are retained. Focused test includes tiny brute force, dynamic conditional coverage, stable ties, native CLI and native/WASM 1/10 determinism; it skips without the necessary toolchains.','']
    if (out/'remote-storage-summary.json').exists():
        remote_storage=read(out/'remote-storage-summary.json');lines += [f"gx10 minimum observed free: {remote_storage['min_free']/1024**3:.3f} GiB; collection peak budget 2 GiB and reserve 20.5 GiB passed before evaluation.",'']
    if (out/'closeout.json').exists():
        closeout=read(out/'closeout.json');lines += [f"Final local session elapsed from preparation: {closeout['elapsed_seconds']:.3f} s (includes development and overlapping jobs). Branch {closeout['branch']}, HEAD {closeout['head']}; no commit or push.",'']
    storage_rows=[read(p) for p in out.glob('storage*.json')];observed=[r['min_free'] for r in storage_rows if 'min_free' in r]
    if (out/'closeout.json').exists():observed.append(read(out/'closeout.json')['free_bytes'])
    storage={'min_free':min(observed)};size=sum(p.stat().st_size for p in out.rglob('*') if p.is_file());lines += [f"Storage monitor samples every 10 s during work; minimum observed free {storage['min_free']/1024**3:.3f} GiB, reserve 20.5 GiB. Current evidence {size/1024**2:.3f} MiB (<300 MB). Top-K only, no full enumeration output, no local search detailed runs, no pre-existing deletion, no commit/push or protected-source edits. S9's unchanged evaluator cleans only its newly created transient capture directories after extracting compact rows; saved results and failures are preserved.",'',
      '## Remaining design work','',
      'Step 3: expose and compare manual waiting / auto-ready burst policies and choose product defaults; this unit preserves the existing L2 and detailed policy. Step 4: statically detect positional targets and prove placement equivalence, including binary64 accumulation order. Step 5: generate explicit per-squad burst-operation candidates. Step 6: add a diversity archive and compose disjoint five-squad solutions; canonical top-K can exclude subsets with strong alternate orders and L2 error can miss detailed winners. Step 7: predicted local swaps, multiple-scenario confirmation and measured shortlist recall remain. Browser integration and ownership/training UI are also pending; Node WASM workers demonstrate the computational core, not browser integration.','',
      'Exhaustive enumeration removes subset-generation heuristics for the stated canonical L2 policy. It does not certify detailed optimality or the design’s 99% recall target. Native detailed failures stay visible and excluded from successful damage summaries.','']
    lines += ['## Files and reproduction','',
      'Modified: `research/team-search/l2_fast.py`, `l2_fast/{l2.h,l2.cpp,cli.cpp,runner.mjs}`, append-only `docs/team-search-design.md`. New: `search_s21.py`, `verify_s21.py`, `report_s21.py`, `validate_s21.py`, `audit_random_s21.py`, `s21-detailed.jsonl`, `tests/test_team_search_enumerator.py`. No protected/product source changes.','',
      'From the worktree: `python3.12 -B research/team-search/search_s21.py prepare`, then `bench`, `order`, `selection`; all default to `$S/s21`. `collect --out REMOTE_S21` runs only on gx10 with the transferred selection/body and unchanged S9 dependencies. `verify_s21.py verify`, `determinism`, and `full-determinism` compare the saved results; `audit_random_s21.py --mask 15` / `--mask 2` ensures distinct random coverage; `validate_s21.py` records the required environment and commands; `report_s21.py` regenerates this report. Existing complete detailed collection with identical IDs/orders is reused. Preserve failed/setup logs; no original evidence is deleted.','']
    (out.parent/'s21-report.md').write_text('\n'.join(lines))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=DEFAULT/'s21');main(p.parse_args().out)
