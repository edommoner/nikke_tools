"""S26 dev-only evaluation and exclusive final-once sealed evaluation."""
import argparse
import json
from pathlib import Path
import l2_fast
import evaluate_s22
import truth_s26 as truth


def score_split(out, profiles, split):
    path=truth.HERE/f's26-{split}.jsonl'
    seal=truth.old.previous.read(out/'seal.json')
    assert truth.old.digest(path)==seal['files'][split]['sha256']
    data={r['id']:r for r in map(json.loads,path.read_text().splitlines())}
    groups=[g for g in truth.old.previous.read(out/'selection.json')['groups'] if g['split']==split]
    rows=[data[g['best']] for g in groups if data[g['best']]['status']=='ok']
    scorer=l2_fast.Score(profiles)
    result=truth.old.metrics(rows,scorer.score_many([r['order'] for r in rows]))
    choices=dict(strict_win=0,tied_win=0,loss=0,incomplete=0)
    for g in groups:
        if not g['order_sample']:continue
        orders=[data[g[k]] for k in ('best','canonical','second')]
        if any(r['status']!='ok' for r in orders):choices['incomplete']+=1;continue
        pred=scorer.score_many([r['order'] for r in orders])
        chosen=min(range(3),key=lambda i:(-pred[i],truth.old.r_order(orders[i],scorer)))
        distinct={tuple(r['order']):r['total'] for r in orders}
        best=max(distinct.values());actual=orders[chosen]['total']
        choices['loss' if actual<best else ('tied_win' if list(distinct.values()).count(best)>1 else 'strict_win')]+=1
    scorer.close()
    result.update(order_choices=choices,failures=len(groups)-len(rows),
        order_choice_domain='three predeclared v3 orders; only v3 best certified across all120')
    return result


def objective(m):
    return (m['recall']['10']['100'],-m['confirmation_depth']['10'],
            -m['confirmation_depth']['1'],m['spearman'])


def dev(out,path,label):
    profiles=truth.old.previous.read(path)
    current=score_split(out,profiles,'dev');guard=evaluate_s22.holdout(profiles)
    baseline=truth.old.previous.read(out/'baseline-dev.json')['v3']
    bg=baseline['S9_holdout']
    passed=guard['spearman']>=bg['spearman']-.005 and guard['recall']['100']['0.05']>=bg['recall']['100']['0.05']
    record=dict(label=label,time=truth.now(),profiles=str(path),profiles_sha256=truth.old.digest(path),
        dev=current,S9_holdout=guard,baseline_S9_holdout=bg,guard_pass=passed,
        improves=passed and objective(current)>objective(baseline))
    with (out/'candidates.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    print(json.dumps(record))


def final(out,path):
    frozen=truth.old.previous.read(out/'model-frozen.json')
    assert truth.old.digest(path)==frozen['profiles_sha256']
    for file,digest in frozen['required_evidence'].items():
        assert truth.old.digest(out/file)==digest,file
    event=dict(started_at=truth.now(),profiles_sha256=truth.old.digest(path),seal_sha256=truth.old.digest(out/'seal.json'))
    # Exclusive creation precedes the first sealed truth read. A failed
    # evaluation consumes the receipt too; no rerun is possible.
    truth.save(out/'final-once.json',event)
    results={label:score_split(out,p,'sealed') for label,p in [
        ('v2',truth.old.previous.profiles(out,15)),
        ('v3',truth.old.previous.read(out.parent/'s22/final-profiles.json')),
        ('adopted',truth.old.previous.read(path))]}
    # Only after the exclusive final opening: summarize discovery outcomes.
    # Excluded S22-sealed subsets remain secondary collection records and
    # cannot affect the already-frozen adoption decision.
    selection=truth.old.previous.read(out/'selection.json')
    best_ids={g['best'] for g in selection['groups']}
    allrows=[json.loads(l) for l in (out/'s21-detailed.jsonl').read_text().splitlines()]
    best=sorted([r for r in allrows if r['id'] in best_ids and r['status']=='ok'],key=lambda r:(-r['total'],r['id']))
    measured=sorted([r for r in allrows if r['status']=='ok'],key=lambda r:(-r['total'],r['id']))
    truth.save(out/'final-evaluation.json',dict(**event,completed_at=truth.now(),metrics=results,
        whole_shortlist=dict(successes=len(best),failures=len(best_ids)-len(best),max=best[0]['total'],
            top10_mean=sum(r['total'] for r in best[:10])/10,top10=best[:10],
            note='All10000 retained v3-best orders; includes1742 quarantined subsets as secondary discovery records only.'),
        all_measured_orders=dict(successes=len(measured),best=measured[0])))
    print(json.dumps(results))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('dev','final'))
    p.add_argument('--out',type=Path,default=truth.DEFAULT)
    p.add_argument('--profiles',type=Path,required=True)
    p.add_argument('--label',default='candidate')
    a=p.parse_args()
    if a.action=='dev':dev(a.out,a.profiles,a.label)
    else:final(a.out,a.profiles)
