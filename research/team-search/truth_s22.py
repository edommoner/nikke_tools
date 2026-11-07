"""S22 dense shortlist truth, subset sealing, and dev-only baseline.

No model modification. All detailed execution uses S21's gx10 collector.
The sealed file is opened for writing at seal time; metric code only reads dev.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import search_s21 as previous

HERE = Path(__file__).resolve().parent
RESERVE = int(20.5 * 1024**3)
BUDGET = 300 * 1024**2


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def subset_key(members):
    return hashlib.sha256(json.dumps(sorted(members), ensure_ascii=False,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def prepare(out):
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise RuntimeError('Preparation requires an empty scratch directory')
    src = out.parent/'s21'
    names = previous.read(src/'rosters.json')['names']
    candidates = previous.read(src/'orders-206-15.json')['rows']
    assert len(candidates) == 10000
    keys = [subset_key([names[i] for i in r['indices']]) for r in candidates]
    assert len(set(keys)) == 10000
    # Exact 50/50 split, independent of scores/truth. Sampling is independently
    # domain-separated and chosen before detailed collection.
    dev = set(sorted(keys)[:5000])
    sample = set(sorted(keys, key=lambda k: hashlib.sha256(('S22-order:'+k).encode()).hexdigest())[:1000])
    rows, lookup, groups = [], {}, []
    def add(indices):
        order = tuple(names[i] for i in indices)
        if order not in lookup:
            lookup[order] = len(rows)
            rows.append(dict(id=len(rows), members=list(order)))
        return lookup[order]
    for r, key in zip(candidates, keys):
        g = dict(key=key, split='dev' if key in dev else 'sealed',
                 best=add(r['best']['indices']), order_sample=key in sample)
        if key in sample:
            g.update(canonical=add(r['indices']), second=add(r['alternates'][0]['indices']))
        groups.append(g)
    save(out/'selection.json', dict(rows=rows, groups=groups))
    (out/'bodies.json').write_bytes((src/'bodies.json').read_bytes())
    cached = {tuple(r['order']):r for r in map(json.loads, (HERE/'s21-detailed.jsonl').read_text().splitlines())}
    reused = []
    for r in rows:
        if tuple(r['members']) not in cached:
            continue
        c = cached[tuple(r['members'])]
        reused.append(dict(id=r['id'], members=r['members'], total_damage=c['total'],
                           backend=c['backend'], reuse='S21 identical ordered squad'))
    with (out/'native-journal.jsonl').open('x') as f:
        for r in reused:
            f.write(json.dumps(r, ensure_ascii=False)+'\n')
    save(out/'prepared.json', dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        subsets=10000, order_sample=1000, unique_orders=len(rows), reused=len(reused),
        split_rule='SHA256(UTF-8 compact JSON sorted member names, ensure_ascii=False); lexicographically lowest 5000 hashes dev, rest sealed',
        sample_rule='lowest 1000 SHA256(ASCII S22-order: + subset hex hash)',
        selection_sha256=digest(out/'selection.json'), source_orders_sha256=digest(src/'orders-206-15.json'),
        reused_source_sha256=digest(HERE/'s21-detailed.jsonl')))


def monitor(out):
    samples = []
    start = shutil.disk_usage(out).free
    while not (out/'MONITOR_STOP').exists():
        free = shutil.disk_usage(out).free
        samples.append(dict(time=time.time(), free_bytes=free))
        save(out/'storage.json', dict(start_free=start, current_free=free,
             min_free=min(r['free_bytes'] for r in samples), samples=samples))
        if free < RESERVE:
            save(out/'STORAGE_STOP.json', dict(time=time.time(), free_bytes=free))
            raise RuntimeError('20.5 GiB floor crossed: stop work')
        time.sleep(10)


def seal(out):
    if (out/'seal.json').exists():
        raise RuntimeError('Already sealed')
    selection = previous.read(out/'selection.json')
    data = [json.loads(l) for l in (out/'s21-detailed.jsonl').read_text().splitlines()]
    byid = {r['id']:r for r in data}
    assert len(byid) == len(selection['rows']) == len(data)
    for r in selection['rows']:
        assert byid[r['id']]['order'] == r['members']
    paths = {}
    for split in ('dev', 'sealed'):
        wanted = {g[k] for g in selection['groups'] if g['split']==split
                  for k in ('best', 'canonical', 'second') if k in g}
        path = HERE/f's22-{split}.jsonl'
        with path.open('x') as f:
            for i in sorted(wanted):
                f.write(json.dumps(byid[i], ensure_ascii=False, separators=(',', ':'))+'\n')
        paths[split] = dict(path=str(path), sha256=digest(path), rows=len(wanted),
                           failures=[r for r in data if r['id'] in wanted and r['status']!='ok'])
    save(out/'seal.json', dict(sealed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         files=paths, prepared=previous.read(out/'prepared.json'),
         collection=previous.read(out/'collection.json')))


def metrics(rows, predictions):
    import measure_s9 as s9
    result = s9.rank_metrics(predictions, [r['total'] for r in rows])
    truth = sorted(range(len(rows)), key=lambda i:(-rows[i]['total'], rows[i]['id']))
    ranked = sorted(range(len(rows)), key=lambda i:(-predictions[i], rows[i]['id']))
    rank = {i:j+1 for j,i in enumerate(ranked)}
    result['recall'] = {str(k): {str(n):len(set(truth[:k]) & set(ranked[:n]))/min(k,len(rows))
                               for n in (10,30,100,300,1000)} for k in (1,10,50)}
    result['confirmation_depth'] = {str(k):max(rank[i] for i in truth[:k]) for k in (1,10)}
    return result


def baseline(out):
    import l2_fast
    selection = previous.read(out/'selection.json')
    # Deliberately no general split argument: dev cannot open sealed rows.
    data = [json.loads(l) for l in (HERE/'s22-dev.jsonl').read_text().splitlines()]
    assert digest(HERE/'s22-dev.jsonl') == previous.read(out/'seal.json')['files']['dev']['sha256']
    byid = {r['id']:r for r in data}
    groups = [g for g in selection['groups'] if g['split']=='dev']
    rows = [byid[g['best']] for g in groups if byid[g['best']]['status']=='ok']
    result = {}
    for mask in (15,2):
        p = previous.profiles(out,mask)
        scorer = l2_fast.Score(p)
        pred = scorer.score_many([r['order'] for r in rows])
        result[str(mask)] = metrics(rows,pred)
        choices = dict(strict_win=0, tied_win=0, loss=0, incomplete=0)
        for g in groups:
            if not g['order_sample']:continue
            orders = [byid[g[k]] for k in ('best','canonical','second')]
            if any(r['status']!='ok' for r in orders):
                choices['incomplete']+=1;continue
            # Re-evaluate order choice among the three predeclared orders for
            # each mask; for mask15 index0 is the all-120 L2 choice.
            ps = scorer.score_many([r['order'] for r in orders])
            chosen = min(range(3), key=lambda i:(-ps[i], r_order(orders[i],scorer)))
            unique = {tuple(r['order']):r['total'] for r in orders}
            best = max(unique.values()); value=orders[chosen]['total']
            choices['loss' if value<best else ('tied_win' if sum(v==best for v in unique.values())>1 else 'strict_win')]+=1
        result[str(mask)]['order_choices'] = choices
        scorer.close()
    save(out/'baseline-dev.json', result)
    print(json.dumps(result))


def r_order(row, scorer):
    return [scorer.index[n] for n in row['order']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','collect','seal','baseline','monitor'))
    parser.add_argument('--out',type=Path,default=previous.DEFAULT/'s22')
    args = parser.parse_args()
    if args.action=='collect':previous.collect(args.out)
    else:globals()[args.action](args.out)
