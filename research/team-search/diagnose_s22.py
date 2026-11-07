"""S22 dev-only residual selection and paired gx10 source observations."""
import argparse
import ast
import collections
import inspect
import json
import math
from pathlib import Path
import subprocess
import sys
import textwrap

import truth_s22 as truth


def group_predictions(profiles, squad):
    """Observe unchanged Python L2 group arithmetic at its contribution line."""
    import l2_score_s20
    source, start = inspect.getsourcelines(l2_score_s20.Score.member_scores)
    tree = ast.parse(textwrap.dedent(''.join(source)))
    node = next(n for n in ast.walk(tree) if isinstance(n,ast.AugAssign)
                and ast.unparse(n.target)=='value')
    line = start+node.lineno-1
    code = l2_score_s20.Score.member_scores.__code__
    groups = []
    def trace(frame,event,arg):
        if frame.f_code is not code:return None
        if event=='line' and frame.f_lineno==line:
            v=frame.f_locals;g=v['g']
            groups.append(dict(member=v['n'],kind=g['kind'],phase=g['phase'],
                unit=v['unit'],scale=v['scale'],base=v['base'],formed=v['formed'],
                combined=v['combined'],inputs=v['own'],
                predicted=v['unit']*math.prod(v['combined'])*v['scale']))
        return trace
    scorer = l2_score_s20.Score(profiles)
    previous = sys.gettrace()
    sys.settrace(trace)
    try:members=scorer.member_scores(squad)
    finally:sys.settrace(previous)
    return dict(members=members,groups=groups)


def prepare(out):
    import l2_fast
    out.mkdir(exist_ok=False)
    parent=out.parent
    rows=[json.loads(l) for l in (truth.HERE/'s22-dev.jsonl').read_text().splitlines()]
    byid={r['id']:r for r in rows}
    groups=truth.previous.read(parent/'selection.json')['groups']
    best=[byid[g['best']] for g in groups if g['split']=='dev' and byid[g['best']]['status']=='ok']
    profiles=truth.previous.profiles(parent,15)
    scorer=l2_fast.Score(profiles)
    predictions=scorer.score_many([r['order'] for r in best])
    errors=sorted([(math.log(p/r['total']),r) for p,r in zip(predictions,best)],key=lambda x:(x[0],x[1]['id']))
    chosen=errors[:50]+errors[-50:]
    selected=[]
    for error,row in chosen:
        values=scorer.member_scores(row['order'])
        selected.append(dict(id=row['id'],target=max(values,key=values.get),members=row['order'],
            context='dev-tail-lowest-signed-error' if (error,row) in errors[:50] else 'dev-tail-highest-signed-error',
            log_error=error,truth=row['total'],l2=sum(values.values()),
            l2_groups=group_predictions(profiles,row['order'])))
    scorer.close()
    truth.save(out/'selection.json',dict(selected=selected,rule='lowest50 + highest50 signed log(prediction/truth), successful dev best orders only',
        dev_sha256=truth.digest(truth.HERE/'s22-dev.jsonl'),profiles_sha256=truth.digest(parent.parent/'s20/dev/final-profiles.json')))
    body=truth.previous.read(parent/'bodies.json')[0]
    body['compute_backend']='cpu'
    truth.save(out/'body.json',body)


def evaluate(body,target,logged):
    import bucket_log
    proc=subprocess.run([sys.executable,'-B',str(bucket_log.ROOT/'research/team-search/observe_s22.py')],
        input=json.dumps(dict(body=body,target=target,logged=logged)),text=True,capture_output=True,timeout=1800)
    if proc.returncode:raise RuntimeError(proc.stderr[-6000:])
    return json.loads(proc.stdout)


def run(out,workers):
    import measure_s18 as runner
    if not str(runner.b.ROOT).startswith('/home/'):
        raise RuntimeError('gx10-only reference observations')
    runner.evaluate=evaluate
    runner.run(out,workers,None)


def summarize(out):
    """Exact ordered algebraic allocation, explicitly not causal mechanisms."""
    import l2_score_s20
    records=[json.loads(p.read_text()) for p in sorted((out/'runs').glob('*.json'))]
    profiles=truth.previous.profiles(out.parent,15)
    totals=collections.Counter();absolute=collections.Counter();denominator=0.
    rows=[]
    labels=['hit/event quantity','f1 coefficients','f2 ATK DEF transfer',
            'f3 crit core caps','f4 charge','f5 damage buffs','f6 received damage','f7 element']
    for r in records:
        if not r['non_interference'] or r['payload_digest']!=r['baseline_digest']:
            raise AssertionError('Observation interference')
        selection=r['selection'];p=r['profile'];pred=selection['l2_groups']
        predicted=sum(pred['members'].values());actual=r['total_damage']
        error=math.log(predicted/actual);denominator+=abs(error)
        weight=error/(predicted-actual) if predicted!=actual else 1./actual
        observed={(g['member'],g['kind'],g['phase']):g for g in p['factor_groups_s22']}
        allocations=collections.Counter();matched_delta=0.;groups=[]
        for g in pred['groups']:
            a=observed.get((g['member'],g['kind'],g['phase']))
            if not a:continue
            values=[g['unit']*g['scale'],*g['combined']]
            truth_values=[a['prefix_sums'][0],*a['effective_buckets']]
            if any(v is None or v<=0 for v in values+truth_values):continue
            logs=[math.log(x/y) for x,y in zip(values,truth_values)]
            logsum=sum(logs)
            delta=g['predicted']-a['damage'];matched_delta+=delta
            multiplier=delta/logsum if abs(logsum)>1e-12 else a['damage']
            for label,term in zip(labels,logs):allocations[label]+=weight*multiplier*term
            groups.append(dict(member=g['member'],kind=g['kind'],phase=g['phase'],
                predicted=g['predicted'],reference=a['damage'],log_components=dict(zip(labels,logs))))
        allocations['unmatched hits and dependencies']=weight*((predicted-actual)-matched_delta)
        # Roundoff should be tiny; preserve it separately instead of assigning
        # it to a purported game mechanism.
        allocations['arithmetic remainder']=error-sum(allocations.values())
        for k,v in allocations.items():totals[k]+=v;absolute[k]+=abs(v)
        casts,fb,cycles=l2_score_s20.cycle(selection['members'],profiles['characters'],profiles['settings']['duration'])
        actual_casts=collections.Counter(e['character'] for e in p['burst_timeline'] if '사용' in e['event'])
        rows.append(dict(id=selection['id'],log_error=error,allocations=dict(allocations),groups=groups,
            members={n:dict(predicted=pred['members'][n],reference=p['member_damage'].get(n,0),
                           predicted_casts=casts[n],reference_casts=actual_casts[n]) for n in selection['members']},
            predicted_fb=fb,reference_fb=p['phase_seconds'][1],predicted_cycles=cycles,reference_cycles=p['cycles'],
            native_reference_total_equal=selection['truth']==actual))
    result=dict(squads=len(records),paired_payload_equalities=len(records),reference_calls=2*len(records),
        native_reference_total_equalities=sum(r['native_reference_total_equal'] for r in rows),
        landed_hits=sum(r['profile']['landed_hits'] for r in records),
        baseline_seconds=sum(r['baseline_seconds'] for r in records),logged_seconds=sum(r['logged_seconds'] for r in records),
        absolute_squad_log_error=denominator,signed_allocations=dict(totals),
        absolute_allocations=dict(absolute),absolute_allocation_shares={k:v/denominator for k,v in absolute.items()},
        note='Ordered telescoping factor allocation on selected dev extremes, not independent causal mechanism shares or a population estimate. Absolute shares may exceed100% through cancellation.',rows=rows)
    truth.save(out/'diagnosis.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run','summarize'))
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=10)
    args=parser.parse_args()
    if args.action=='prepare':prepare(args.out)
    elif args.action=='run':run(args.out,args.workers)
    else:summarize(args.out)
