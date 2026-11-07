"""S22 v3 S21-pipeline rerun; detailed reuse only AFTER sealed evaluation."""
import argparse
import ctypes as C
import itertools
import json
from pathlib import Path
import time
import truth_s22 as truth


def prepare(out):
    import l2_fast
    out.mkdir(exist_ok=False)
    p=truth.previous.read(out.parent/'final-profiles.json')
    score=l2_fast.Score(p)
    (out/'v3.l2ft').write_bytes(score.raw);score.close()
    for name in ('rosters.json','roster-150.json','roster-206.json','bodies.json'):
        (out/name).write_bytes((out.parent.parent/'s21'/name).read_bytes())
    truth.save(out/'identity.json',dict(profiles_sha256=truth.digest(out.parent/'final-profiles.json'),
        table_sha256=truth.digest(out/'v3.l2ft')))


def enumerate_roster(out,n,legacy=False):
    import l2_fast
    if truth.digest(out.parent/'final-profiles.json')!=truth.previous.read(out/'identity.json')['profiles_sha256']:
        raise ValueError('Model changed')
    target=out/f'{"legacy" if legacy else "v3"}-{n}.json'
    if target.exists():raise RuntimeError('Enumeration already recorded')
    p=truth.previous.profiles(out.parent,15) if legacy else truth.previous.read(out.parent/'final-profiles.json')
    score=l2_fast.Score(p);started=time.perf_counter()
    result=l2_fast.enumerate_top(score,truth.previous.read(out/f'roster-{n}.json'),10000,10,1)
    score.close();result.update(wall_seconds=time.perf_counter()-started,threads=10,version=2 if legacy else 3)
    truth.save(target,result)
    if legacy:
        old=truth.previous.read(out.parent.parent/f's21/native-{n}-15-10-1.json')
        assert result['entries']==old['entries']
        assert all(result['counts'][k]==old['counts'][k] for k in ('visited','covered','scored'))
        truth.save(out/f'legacy-{n}-identical.json',dict(entries=10000,differences=0,counts_identical=True))
    print(n,legacy,result['counts'],result['wall_seconds'],flush=True)


def order(out,n):
    import l2_fast
    source=truth.previous.read(out/f'v3-{n}.json')['entries']
    score=l2_fast.Score.load(out.parent/'final-profiles.json');rows=[];started=time.perf_counter()
    for offset in range(0,len(source),64):
        batch=source[offset:offset+64]
        orders=[list(s) for r in batch for s in itertools.permutations(r['indices'])]
        values=score.score_indices((C.c_uint32*(len(orders)*5))(*(i for s in orders for i in s)))
        for j,r in enumerate(batch):
            candidates=sorted([dict(indices=orders[j*120+i],score=values[j*120+i]) for i in range(120)],key=lambda r:(-r['score'],r['indices']))
            rows.append(dict(indices=r['indices'],canonical_score=r['score'],best=candidates[0],alternates=candidates[1:3]))
    rows.sort(key=lambda r:(-r['best']['score'],r['indices']));score.close()
    truth.save(out/f'orders-{n}.json',dict(rows=rows,seconds=time.perf_counter()-started,orders_scored=len(rows)*120))


def selection(out):
    names=truth.previous.read(out/'rosters.json')['names'];rows=[];lookup={};groups={}
    for n in (206,150):
        ids=[]
        for r in truth.previous.read(out/f'orders-{n}.json')['rows'][:300 if n==206 else 100]:
            squad=tuple(names[i] for i in r['best']['indices'])
            if squad not in lookup:
                lookup[squad]=len(rows);rows.append(dict(id=len(rows),members=list(squad)))
            ids.append(lookup[squad])
        groups[str(n)]=ids
    truth.save(out/'selection.json',dict(rows=rows,groups=groups))


def collect(out):
    if not str(out).startswith('/home/'):raise RuntimeError('gx10-only')
    truth.previous.collect(out)


def reuse(out):
    # The shortlist preparation above has no detailed truth access. This stage
    # is explicitly forbidden until the exclusive final evaluation completed.
    if not (out.parent/'final-evaluation.json').exists():raise RuntimeError('Final sealed evaluation required first')
    source={tuple(r['order']):r for path in (out.parent/'s21-detailed.jsonl',truth.HERE/'s21-detailed.jsonl')
            for r in map(json.loads,path.read_text().splitlines())}
    rows=truth.previous.read(out/'selection.json')['rows'];reused=[]
    for r in rows:
        if tuple(r['members']) in source:
            old=source[tuple(r['members'])]
            reused.append(dict(id=r['id'],members=r['members'],total_damage=old['total'],backend=old['backend'],reuse='identical ordered S21/S22 result'))
    with (out/'native-journal.jsonl').open('x') as f:
        for r in reused:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    truth.save(out/'reuse.json',dict(requested=len(rows),reused=len(reused),new=len(rows)-len(reused)))


def summarize(out):
    rows={r['id']:r for r in map(json.loads,(out/'s21-detailed.jsonl').read_text().splitlines())}
    names=truth.previous.read(out/'rosters.json')['names'];summary={}
    for n,ids in truth.previous.read(out/'selection.json')['groups'].items():
        orders=truth.previous.read(out/f'orders-{n}.json')['rows'][:len(ids)]
        selected=[rows[i] for i in ids];valid=[(r,o) for r,o in zip(selected,orders) if r['status']=='ok']
        actual=sorted((r['total'] for r,o in valid),reverse=True)
        summary[n]=dict(requested=len(ids),successes=len(valid),max=actual[0],top10_mean=sum(actual[:10])/10,
            **truth.metrics([r for r,o in valid],[o['best']['score'] for r,o in valid]))
    truth.save(out/'summary.json',summary);print(json.dumps(summary))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','enumerate','legacy','order','selection','reuse','collect','summarize'))
    parser.add_argument('--out',type=Path,default=truth.previous.DEFAULT/'s22/search')
    parser.add_argument('--roster',type=int,choices=(150,206))
    a=parser.parse_args()
    if a.action in ('enumerate','legacy'):enumerate_roster(a.out,a.roster,a.action=='legacy')
    elif a.action=='order':order(a.out,a.roster)
    else:globals()[a.action](a.out)
