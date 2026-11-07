"""S22 dev candidate ledger and exclusively guarded final evaluation."""
import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import random
import l2_fast
import truth_s22 as truth


def score_split(out, profiles, split):
    path=truth.HERE/f's22-{split}.jsonl'
    seal=truth.previous.read(out/'seal.json')
    if truth.digest(path)!=seal['files'][split]['sha256']:raise ValueError('Truth identity changed')
    data=[json.loads(l) for l in path.read_text().splitlines()]
    byid={r['id']:r for r in data}
    groups=[g for g in truth.previous.read(out/'selection.json')['groups'] if g['split']==split]
    rows=[byid[g['best']] for g in groups if byid[g['best']]['status']=='ok']
    scorer=l2_fast.Score(profiles)
    result=truth.metrics(rows,scorer.score_many([r['order'] for r in rows]))
    choices=dict(strict_win=0,tied_win=0,loss=0,incomplete=0)
    for g in groups:
        if not g['order_sample']:continue
        orders=[byid[g[k]] for k in ('best','canonical','second')]
        if any(r['status']!='ok' for r in orders):choices['incomplete']+=1;continue
        pred=scorer.score_many([r['order'] for r in orders])
        selected=min(range(3),key=lambda i:(-pred[i],truth.r_order(orders[i],scorer)))
        distinct={tuple(r['order']):r['total'] for r in orders}
        best=max(distinct.values());actual=orders[selected]['total']
        choices['loss' if actual<best else ('tied_win' if list(distinct.values()).count(best)>1 else 'strict_win')]+=1
    result['order_choices']=choices
    result['order_choice_domain']='three predeclared orders; only v2 mask15 best is certified across all120'
    result['failures']=len(groups)-len(rows)
    scorer.close()
    return result


def holdout(profiles):
    import measure_s9 as s9
    rows=s9.valid(s9.read(s9.HERE/'s9-dataset.jsonl'))
    random.Random(45).shuffle(rows);rows=rows[10000:]
    scorer=l2_fast.Score(profiles)
    result=s9.metrics(rows,[math.log(v) for v in scorer.score_many([r['members'] for r in rows])])
    scorer.close()
    return result


def dev(out,path,label,profiles=None):
    supplied=profiles is not None
    profiles=profiles if supplied else truth.previous.read(path)
    current=score_split(out,profiles,'dev');guard=holdout(profiles)
    baseline=truth.previous.read(out/'baseline-dev.json')['15']
    baseline_guard=holdout(truth.previous.profiles(out,15))
    guard_pass=(guard['spearman']>=baseline_guard['spearman']-.005 and
                guard['recall']['100']['0.05']>=baseline_guard['recall']['100']['0.05'])
    def objective(m):
        return (m['recall']['10']['100'],-m['confirmation_depth']['10'],
                -m['confirmation_depth']['1'],m['spearman'])
    record=dict(label=label,time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        profiles=str(path),profiles_sha256=(hashlib.sha256((json.dumps(profiles,ensure_ascii=False,separators=(',',':'))+'\n').encode()).hexdigest() if supplied else truth.digest(path)),dev=current,S9_holdout=guard,
        baseline_S9_holdout=baseline_guard,guard_pass=guard_pass,
        eligible=guard_pass and objective(current)>objective(baseline),
        criterion='lexicographic dev top10 recall@100, lower depth10, lower depth1, Spearman; S9 guard')
    if supplied:record['profile_derivation']=dict(base_sha256=truth.digest(path),s22_switches=profiles['s22']['switches'],serialization='UTF8 ensure_asciiFalse compact JSON plus newline')
    with (out/'candidates.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps(record))


def final(out,path):
    frozen=truth.previous.read(out/'model-frozen.json')
    if truth.digest(path)!=frozen['profiles_sha256']:raise ValueError('Final model changed')
    for name,hash_value in frozen['required_evidence'].items():
        if truth.digest(out/name)!=hash_value:raise ValueError('Frozen evidence changed: '+name)
    event=dict(started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        profiles_sha256=truth.digest(path),seal_sha256=truth.digest(out/'seal.json'))
    # Written exclusively BEFORE any sealed truth is opened or scored; even a
    # failed final attempt consumes the guard.
    with (out/'final-once.json').open('x') as f:json.dump(event,f,indent=2)
    results={name:score_split(out,p,'sealed') for name,p in
             [('v2-mask15',truth.previous.profiles(out,15)),('v3-final',truth.previous.read(path))]}
    selection=truth.previous.read(out/'selection.json')
    wanted={g['best'] for g in selection['groups']}
    allrows=[json.loads(l) for split in ('dev','sealed') for l in (truth.HERE/f's22-{split}.jsonl').read_text().splitlines()]
    rows=sorted([r for r in allrows if r['id'] in wanted and r['status']=='ok'],key=lambda r:(-r['total'],r['id']))
    truth.save(out/'final-evaluation.json',dict(**event,metrics=results,
        whole_shortlist=dict(successes=len(rows),failures=10000-len(rows),top10=rows[:10],
                             max=rows[0]['total'],top10_mean=sum(r['total'] for r in rows[:10])/10),
        completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print(json.dumps(results))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('dev','final'))
    parser.add_argument('--profiles',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=truth.previous.DEFAULT/'s22')
    parser.add_argument('--label',default='candidate')
    args=parser.parse_args()
    if args.action=='dev':dev(args.out,args.profiles,args.label)
    else:final(args.out,args.profiles)
