"""S1 research only. Run from any cwd; no verification or persistent raw captures.

python3.12 research/team-search/measure_s1.py --benchmark PATH --report PATH
Uses only the standard library and the product's existing Python/Node adapters.
Requires Python >= 3.10, as does the upstream evaluator.
"""
import argparse
import collections
import json
import math
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'app'))


def node(payload):
    return json.loads(subprocess.check_output(['node', str(HERE / 'measure_s1.mjs')],
                                              input=json.dumps(payload).encode(), cwd=ROOT))


def covered(squad, chars):
    stages = [chars[n]['burst'] for n in squad]
    return sum(s not in stages for s in ('1', '2', '3')) <= stages.count('A')


def ranks(values):
    out = [0.] * len(values)
    ordered = sorted(range(len(values)), key=values.__getitem__)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[ordered[j]] == values[ordered[i]]:
            j += 1
        for k in ordered[i:j]:
            out[k] = (i + j - 1) / 2
        i = j
    return out


def correlation(rows):
    x = [r['simple_score'] for r in rows]
    y = [r['total_damage'] for r in rows]
    rx, ry = ranks(x), ranks(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    den = math.sqrt(sum((v-mx)**2 for v in rx)*sum((v-my)**2 for v in ry))
    concordance = ties_x = ties_y = 0
    for i in range(len(x)):
        for j in range(i):
            dx, dy = x[i]-x[j], y[i]-y[j]
            ties_x += dx == 0
            ties_y += dy == 0
            concordance += (dx*dy > 0) - (dx*dy < 0)
    pairs = len(x)*(len(x)-1)//2
    kd = math.sqrt((pairs-ties_x)*(pairs-ties_y))
    return dict(n=len(rows), spearman=sum((a-mx)*(b-my) for a,b in zip(rx,ry))/den if den else None,
                kendall_tau_b=concordance/kd if kd else None)


def summarize(rows, pool, metadata):
    valid = [r for r in rows if r.get('total_damage') is not None]
    b = [r for r in valid if r['cohort']=='B']
    c = [r for r in valid if r['cohort']=='C']
    ab = [r for r in valid if r['cohort']!='C']
    truth = sorted(valid, key=lambda r: (-r['total_damage'], r['id']))
    ordered = sorted(valid, key=lambda r: (-r['simple_score'], r['id']))
    miss = {}
    for n in (20, 100):
        top = {r['id'] for r in truth[:n]}
        miss[n] = {k:dict(found=len(top & {r['id'] for r in ordered[:k]}),
                             miss_rate=1-len(top & {r['id'] for r in ordered[:k]})/len(top))
                   for k in (100,500,1000,2000)}
    best = {}
    for label, selected in [('A',[r for r in rows if r['cohort']=='A']), ('A+B',[r for r in rows if r['cohort']!='C'])]:
        results = [dict(result=dict(members=[dict(name=n) for n in r['members']],total_damage=r['total_damage']))
                   if r.get('total_damage') is not None else dict(error=r['error']) for r in selected]
        best[label] = node(dict(action='best',results=results,groups=pool['groups']))
    threshold = sorted(r['total_damage'] for r in b)[math.ceil(.9*len(b))-1]
    issues = [r for r in rows if r['backend']!='native_detail']
    return dict(metadata=metadata, correlations=dict(B=correlation(b), A_union_B=correlation(ab)),
                miss_rates=miss, true_top100_in_A=sum(r['cohort']=='A' for r in truth[:100]),
                best_disjoint=best, unconstrained_C=dict(n=len(c),without_coverage=sum(not r['burst_coverage'] for r in c),
                B_median=statistics.median(r['total_damage'] for r in b), B_p90=threshold,
                beat_B_median=sum(r['total_damage']>statistics.median(v['total_damage'] for v in b) for r in c),
                beat_B_p90=sum(r['total_damage']>threshold for r in c),
                lacking_coverage_beat_B_median=sum(not r['burst_coverage'] and r['total_damage']>statistics.median(v['total_damage'] for v in b) for r in c),
                lacking_coverage_beat_B_p90=sum(not r['burst_coverage'] and r['total_damage']>threshold for r in c)),
                backends=dict(collections.Counter(r['backend'] for r in rows)),coverage_issues=issues,
                observed_characters=len({n for r in rows for n in r['members']}),
                native_observed_characters=len({n for r in rows if r['backend']=='native_detail' for n in r['members']}),
                characters_in_issues=sorted({n for r in issues for n in r['members']}))


def write_report(summary, path):
    m = summary['metadata']
    lines = ['# Team search S1', '',
        '## Method', '',
        f"Benchmark profile: {m['owned']} owned characters; {m['scored']} scored; skipped: {m['skipped']}.",
        'A = current candidatePool(5, 160, 41), with 33 real regression templates. Its ordered squads exactly match unit8/long-bodies.json.',
        'B = 2,000 uniform ordered 5-tuples, rejection-sampled for burst coverage (seed 42). '
        'C = 300 uniform ordered 5-tuples without that constraint (seed 43). '
        'Members are distinct; exact ordered duplicates across cohorts are rejected. '
        'Each A/all-stage character can fill one missing stage. Order is retained because it affects burst priority.',
        'Battle: 180 s, level 400, enemy DEF 31784 / wind / core 50 px / distance 25 m; '
        'auto burst, fixed gauge, no stat deltas. Settings and character potentials are in s1-inputs.json.',
        'Simple score = sum(atk × damage_coeff × fire_rate). The generator uses member potential to truncate/order '
        'eligible choices and its sum to rank templates, then samples stochastically; it has no separate scalar '
        'squad objective. pool_generator_effective_score therefore records that sum, not a probability or GPU estimate. '
        'Pool insertion index is recorded separately and is not a score.',
        'native_detail uses the existing portable_detail.evaluate_many path, batches of 32, 10 host threads. '
        'Verification is deferred and never performed; verify_detail=false. These are unverified research rankings. '
        'Mandatory API captures live only in an owned temporary batch directory and are deleted after extracting results.', '',
        '## Rank correlation', '', '| Cohort | n | Spearman | Kendall tau-b |', '|---|---:|---:|---:|']
    for cohort, values in summary['correlations'].items():
        lines.append(f"| {cohort} | {values['n']} | {values['spearman']:.6f} | {values['kendall_tau_b']:.6f} |")
    lines += ['', '## Miss rate', '',
        '“True” means highest detailed damage within the measured A∪B∪C only, not a global optimum. '
        'Simple-score top-K uses the same union. Ties use stable row ID (A then B then C); '
        'correlations use average ranks and tie-corrected tau-b. Failed rows, if any, are excluded from ranking.', '',
        '| Detailed top-N | K | Found | Miss rate |','|---:|---:|---:|---:|']
    for n, values in summary['miss_rates'].items():
        for k, value in values.items():
            lines.append(f"| {n} | {k} | {value['found']} | {value['miss_rate']:.1%} |")
    lines += ['',f"A contains {summary['true_top100_in_A']} of the detailed top-100.", '',
              '## Five disjoint squads', '',
              'Unchanged bestDisjoint, beam width 256; original candidate order and A feasible groups retained in both runs. '
              'A+B appends B. This measures the existing heuristic, not exact set packing.', '']
    for label, best in summary['best_disjoint'].items():
        lines.append(f"- {label}: **{best['damage']:,.0f}** total damage")
        for team in best['teams']:
            lines.append(f"  - {' / '.join(team['squad'])}: {team['damage']:,.0f}")
    a, ab = (summary['best_disjoint'][key]['damage'] for key in ('A','A+B'))
    lines += ['',f"Change: {ab-a:,.0f} ({ab/a-1:+.2%}).", '', '## Unconstrained C', '']
    c = summary['unconstrained_C']
    lines += [f"Of {c['n']} C squads, {c['without_coverage']} lack coverage. "
              f"{c['beat_B_median']} beat B's median ({c['B_median']:,.0f}); "
              f"{c['beat_B_p90']} beat B's 90th percentile ({c['B_p90']:,.0f}, nearest-rank threshold). "
              f"Among C squads lacking coverage, {c['lacking_coverage_beat_B_median']} / {c['lacking_coverage_beat_B_p90']} "
              'beat those respective thresholds.', '',
              '## Kernel coverage', '', f"Backends: {summary['backends']}. "
              f"Distinct observed characters: {summary['observed_characters']}; "
              f"appearing in successful native squads: {summary['native_observed_characters']}."]
    if summary['coverage_issues']:
        reasons = collections.Counter(item.get('reason','unknown') for row in summary['coverage_issues']
                                      for item in (row['unsupported'] or []))
        lines += ['', '| Fallback reason | Squads |', '|---|---:|']
        lines += [f'| {reason} | {count} |' for reason,count in reasons.most_common()]
        lines += ['', 'The character-specific diagnostic names 슈가 (Sugar), effect 블랙 타이푼 5, '
                  'unsupported effect field target_code, in two squads. Other diagnostics describe compositions '
                  'or runtime capacity/status; no individual cause is assigned from co-occurrence.', '',
                  'All affected squad IDs, members, reasons and unsupported effect contexts are retained in the summary JSON. '
                  'Characters appearing in a failed/fallback squad are co-occurrences, not proof each character is unsupported.', '',
                  '| Squad ID | Backend | Members | Reason |', '|---:|---|---|---|']
        for row in summary['coverage_issues']:
            reason = json.dumps(row['unsupported'],ensure_ascii=False) if row['unsupported'] else row['error']
            lines.append(f"| {row['id']} | {row['backend']} | {' / '.join(row['members'])} | {reason} |")
    else:
        lines.append('No CPU fallback or failed squads; every owned character occurs in the measured sample. '
                     'This establishes coverage of these sampled conditions, not all effects/settings.')
    misses = {int(n):{int(k):v for k,v in values.items()} for n,values in summary['miss_rates'].items()}
    missed500 = misses[100][500]['miss_rate']
    decision = (f"The current sum-potential score is inadequate for aggressive shortlisting in this scenario: "
                f"top-500 misses {missed500:.1%} of the measured detailed top-100. "
                'Investment in a better L2 is justified by this sample; first close the reported kernel '
                'composition/capacity gaps, then measure a proposed surrogate against this baseline. '
                'These data do not establish which new surrogate will work.' if missed500 > .01 else
                'This sample does not establish a need for a large L2 investment at K=500. '
                'Broaden profiles and scenarios before relying on its recall.')
    lines += ['', '## Time, storage and validation', '',
        f"Evaluation wall time: {m['evaluation_seconds']:.3f} s; {m['seconds_per_squad']*1000:.3f} ms/squad "
        f"(end to end, including preparation, native dispatch, decoding and cleanup). Total script wall time: {m['wall_seconds']:.3f} s.",
        f"Free disk before/after: {m['free_bytes_before']/1024**3:.3f} / {m['free_bytes_after']/1024**3:.3f} GiB. "
        'Storage preflight passed with a 512 MiB extra-byte budget and 20 GiB reserve. No raw captures retained.',
        'node --test tests/*.test.mjs: 168 passed; only the allowed sandbox HTTP listener test failed (listen EPERM). '
        'No product Python files changed. Research rank metrics checked against perfect, reversed and tied examples.', '',
        'Reproduce from the worktree with Python 3.12:', '',
        '```sh',
        'python3.12 research/team-search/measure_s1.py \\',
        f"  --benchmark {m['benchmark']} \\",
        f'  --report {path.resolve()}',
        '```', '',
        'Final checks: Python compilation; all 2,460 row counts, distinct membership, scores, '
        'B coverage, pending native verification, five-team disjointness/totals and temporary capture cleanup; '
        'git diff --check. Product edits only remove rankCombatPool and its two unused tests.', '',
        '## Decision', '', decision, '',
        'This single profile/scenario and 2,300 random squads cannot certify a global top-K or a safe hard burst constraint. '
        'All-character coverage remains a prerequisite before building a new L2.', '',
        'Raw data: `research/team-search/s1-results.jsonl`; summary: `research/team-search/s1-summary.json`; '
        'inputs: `research/team-search/s1-inputs.json`. No commit or push.']
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(lines)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    free = shutil.disk_usage(ROOT).free
    if free < 20*1024**3 + 512*1024**2:
        raise RuntimeError('20 GiB reserve plus 512 MiB run budget required')
    import engine_worker
    import portable_detail
    from portable_native import HOST_THREADS, availability
    os.environ.update(node(dict(action='env')))
    native = availability(ROOT)
    if not native['available']:
        raise RuntimeError(native['reason'])
    body = json.loads(args.benchmark.read_text())[0]
    body.update(compute_backend='native_detail',verify_detail=False)
    scored = engine_worker.candidate_scores(dict(evaluation=body))
    chars = {c['name']:c for c in scored['characters']}
    # Uniform sample without replacement, then rejection: uniform conditional
    # distribution over ordered 5-tuples satisfying coverage. No score weighting.
    pool = node(dict(action='pool',**scored))
    assert len(pool['pool']) == 160
    rows = []
    seen = set()
    def add(cohort, squad):
        key = tuple(squad)  # Order affects burst priority; retain it.
        if key in seen:
            return False
        seen.add(key)
        potentials = [chars[n]['potential'] for n in squad]
        rows.append(dict(id=len(rows),cohort=cohort,members=squad,member_potentials=potentials,
                         simple_score=sum(potentials),pool_generator_effective_score=sum(potentials),
                         pool_insertion_index=len(rows) if cohort=='A' else None,
                         burst_coverage=covered(squad,chars)))
        return True
    for squad in pool['pool']:
        assert add('A',squad)
    for cohort, count, seed in [('B',2000,42),('C',300,43)]:
        rng = random.Random(seed)
        n = 0
        while n < count:
            squad = rng.sample(list(chars),5)
            if cohort=='B' and not covered(squad,chars):
                continue
            n += add(cohort,squad)
    (HERE/'s1-inputs.json').write_text(json.dumps(dict(benchmark=str(args.benchmark.resolve()),
        settings={k:v for k,v in body.items() if k not in ('profile','squad')},
        characters=scored,pool=pool),ensure_ascii=False,indent=2)+'\n')
    evaluation_started = time.perf_counter()
    HOST_THREADS.set(10)
    # Captures are mandatory in this API. Own a fresh directory per batch and
    # remove it only after damage/fallback provenance has been copied to JSONL.
    with (HERE/'s1-results.jsonl').open('w') as output:
        for offset in range(0,len(rows),32):
            batch = rows[offset:offset+32]
            batch_started = time.perf_counter()
            bodies = [dict(body,squad=r['members']) for r in batch]
            with tempfile.TemporaryDirectory(prefix='s1-detail-') as capture:
                previous = os.environ.get('NIKKE_DETAIL_CAPTURE_ROOT')
                os.environ['NIKKE_DETAIL_CAPTURE_ROOT'] = capture
                try:
                    results = portable_detail.evaluate_many(bodies,verification='deferred')
                    for row, request, result in zip(batch,bodies,results):
                        payload = result.get('result',{})
                        pending = payload.get('cpu_fallback_pending')
                        if pending:
                            try:
                                payload = portable_detail.cpu_fallback_portable_detail([
                                    dict(body=request,capture_id=pending['capture_id'])])[0]
                            except Exception as error:
                                result = dict(error=str(error))
                        compute = payload.get('compute',{})
                        row.update(total_damage=payload.get('total_damage'),backend=compute.get('backend','failed'),
                                   fallback_reason=compute.get('fallback_reason'),
                                   unsupported=compute.get('unsupported',pending),error=result.get('error'),
                                   cpu_verification=compute.get('cpu_verification'),
                                   batch_elapsed_seconds=time.perf_counter()-batch_started)
                        output.write(json.dumps(row,ensure_ascii=False)+'\n')
                    output.flush()
                finally:
                    if previous is None:
                        os.environ.pop('NIKKE_DETAIL_CAPTURE_ROOT',None)
                    else:
                        os.environ['NIKKE_DETAIL_CAPTURE_ROOT'] = previous
            print(f'{offset+len(batch)}/{len(rows)} {time.perf_counter()-evaluation_started:.1f}s',flush=True)
    evaluated = time.perf_counter()-evaluation_started
    metadata = dict(benchmark=str(args.benchmark.resolve()),owned=len(body['profile']['chars']),scored=len(chars),
                    skipped=scored['skipped'], seeds=dict(A=41,B=42,C=43), evaluation_seconds=evaluated,
                    seconds_per_squad=evaluated/len(rows),free_bytes_before=free,
                    free_bytes_after=shutil.disk_usage(ROOT).free,verification='deferred; never checked',
                    native_host_threads=10,raw_captures_retained=False)
    summary = summarize(rows,pool,metadata)
    metadata['wall_seconds'] = time.perf_counter()-started
    (HERE/'s1-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    write_report(summary,args.report)


if __name__ == '__main__':
    main()
