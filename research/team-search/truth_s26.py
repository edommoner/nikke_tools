"""Fresh v3 shortlist truth. No model changes or sealed metric access."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time

import truth_s22 as old

HERE = old.HERE
DEFAULT = old.previous.DEFAULT / 's26'
RESERVE = int(20.5 * 1024**3)
BUDGET = 150_000_000


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def prepare(out):
    out.mkdir(exist_ok=True)
    if any(p.name not in ('storage.jsonl', 'preparation-attempt1') for p in out.iterdir()):
        raise RuntimeError('Preparation requires an empty evidence directory')
    src = out.parent / 's22/search-cap'
    names = old.previous.read(src / 'rosters.json')['names']
    candidates = old.previous.read(src / 'orders-206.json')['rows']
    assert len(candidates) == 10000
    # Only membership is used from the already-open S22 sealed file. Its
    # outcomes are never used to select, rank, diagnose, or evaluate a model.
    excluded = {old.subset_key(json.loads(line)['members'])
                for line in (HERE / 's22-sealed.jsonl').read_text().splitlines()}
    pairs = [(r, old.subset_key([names[i] for i in r['indices']])) for r in candidates]
    kept = [(r, k) for r, k in pairs if k not in excluded]
    keys = sorted(k for _, k in kept)
    assert len(set(keys)) == len(keys)
    dev = set(keys[:len(keys)//2])
    sample = set(sorted(keys, key=lambda k: hashlib.sha256(('S22-order:'+k).encode()).hexdigest())[:1000])
    rows, lookup, groups = [], {}, []
    def add(indices):
        order = tuple(names[i] for i in indices)
        if order not in lookup:
            lookup[order] = len(rows)
            rows.append(dict(id=len(rows), members=list(order)))
        return lookup[order]
    for r, key in pairs:
        g = dict(key=key, split=('excluded' if key in excluded else 'dev' if key in dev else 'sealed'),
                 best=add(r['best']['indices']), order_sample=key in sample)
        if key in sample:
            g.update(canonical=add(r['indices']), second=add(r['alternates'][0]['indices']))
        groups.append(g)
    save(out / 'selection.json', dict(rows=rows, groups=groups))
    (out / 'bodies.json').write_bytes((src / 'bodies.json').read_bytes())
    sources = [HERE/'s21-detailed.jsonl', out.parent/'s22/s21-detailed.jsonl',
               src/'s21-detailed.jsonl']
    cached, identities = {}, {}
    for path in sources:
        identities[str(path)] = old.digest(path)
        for line in path.read_text().splitlines():
            r = json.loads(line)
            key = tuple(r['order'])
            if key in cached and cached[key][0]['total'] != r['total']:
                raise ValueError('Conflicting exact-order reuse')
            cached[key] = r, str(path)
    reused = []
    with (out/'native-journal.jsonl').open('x') as f:
        for row in rows:
            hit = cached.get(tuple(row['members']))
            if hit is None:
                continue
            r, source = hit
            # Reuse only successful native rows under the identical S1 body.
            if r['status'] != 'ok' or r['backend'] != 'native_detail':
                continue
            record = dict(id=row['id'], members=row['members'], total_damage=r['total'],
                          backend=r['backend'], reuse=source)
            f.write(json.dumps(record, ensure_ascii=False)+'\n')
            reused.append(dict(id=row['id'], source=source, source_id=r['id']))
    assert (src/'bodies.json').read_bytes() == (out.parent/'s22/bodies.json').read_bytes()
    save(out/'prepared.json', dict(created_at=now(), source_subsets=10000,
         excluded_s22_sealed_subsets=len(pairs)-len(kept), excluded_universe=len(excluded),
         subsets=len(pairs), eligible_subsets=len(kept), dev_subsets=len(dev), sealed_subsets=len(keys)-len(dev),
         order_sample=len(sample), unique_orders=len(rows), reused=len(reused),
         split_rule='S22 sorted subset SHA256; lowest floor(n/2) dev, remaining sealed',
         sample_rule='lowest1000 SHA256(ASCII S22-order: + subset hex hash), after exclusions',
         selection_sha256=old.digest(out/'selection.json'),
         source_orders_sha256=old.digest(src/'orders-206.json'),
         body_sha256=old.digest(out/'bodies.json'), reuse_source_hashes=identities,
         reused_orders=reused))
    print(json.dumps({k:v for k,v in old.previous.read(out/'prepared.json').items() if k!='reused_orders'}))


def seal(out):
    selection = old.previous.read(out/'selection.json')
    data = [json.loads(l) for l in (out/'s21-detailed.jsonl').read_text().splitlines()]
    byid = {r['id']:r for r in data}
    assert len(byid) == len(data) == len(selection['rows'])
    assert all(byid[r['id']]['order'] == r['members'] for r in selection['rows'])
    files = {}
    for split in ('dev', 'sealed'):
        ids = {g[k] for g in selection['groups'] if g['split']==split
               for k in ('best','canonical','second') if k in g}
        path = HERE/f's26-{split}.jsonl'
        with path.open('x') as f:
            for i in sorted(ids):
                f.write(json.dumps(byid[i], ensure_ascii=False, separators=(',',':'))+'\n')
        files[split] = dict(path=str(path), sha256=old.digest(path), rows=len(ids),
                            failures=sum(byid[i]['status']!='ok' for i in ids))
    save(out/'seal.json', dict(sealed_at=now(), files=files,
         prepared_sha256=old.digest(out/'prepared.json'),
         selection_sha256=old.digest(out/'selection.json'),
         collection=old.previous.read(out/'collection.json')))


def baseline(out):
    import l2_fast
    import evaluate_s22
    seal = old.previous.read(out/'seal.json')
    path = HERE/'s26-dev.jsonl'
    assert old.digest(path) == seal['files']['dev']['sha256']
    data = {r['id']:r for r in map(json.loads, path.read_text().splitlines())}
    groups = [g for g in old.previous.read(out/'selection.json')['groups'] if g['split']=='dev']
    rows = [data[g['best']] for g in groups if data[g['best']]['status']=='ok']
    result = {}
    for label, p in [('v2', old.previous.profiles(out,15)),
                     ('v3', old.previous.read(out.parent/'s22/final-profiles.json'))]:
        scorer = l2_fast.Score(p)
        m = old.metrics(rows, scorer.score_many([r['order'] for r in rows]))
        choices = dict(strict_win=0,tied_win=0,loss=0,incomplete=0)
        for g in groups:
            if not g['order_sample']:continue
            orders = [data[g[k]] for k in ('best','canonical','second')]
            if any(r['status']!='ok' for r in orders):
                choices['incomplete']+=1;continue
            pred = scorer.score_many([r['order'] for r in orders])
            chosen = min(range(3), key=lambda i:(-pred[i], old.r_order(orders[i],scorer)))
            distinct = {tuple(r['order']):r['total'] for r in orders}
            actual = orders[chosen]['total']; best = max(distinct.values())
            choices['loss' if actual<best else ('tied_win' if list(distinct.values()).count(best)>1 else 'strict_win')]+=1
        scorer.close()
        m.update(order_choices=choices, failures=len(groups)-len(rows), S9_holdout=evaluate_s22.holdout(p))
        result[label] = m
    save(out/'baseline-dev.json', result)
    print(json.dumps(result))


def monitor(out):
    initial = shutil.disk_usage(out).free
    with (out/'storage.jsonl').open('a') as f:
        while not (out/'MONITOR_STOP').exists():
            free = shutil.disk_usage(out).free
            record = dict(time=now(), free_bytes=free, initial_free_bytes=initial)
            f.write(json.dumps(record)+'\n');f.flush()
            if free < RESERVE:
                save(out/'STORAGE_STOP.json', record)
                return
            time.sleep(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','seal','baseline','collect','monitor'))
    parser.add_argument('--out', type=Path, default=DEFAULT)
    a = parser.parse_args()
    if a.action=='collect':
        old.previous.collect(a.out)
    else:
        globals()[a.action](a.out)
