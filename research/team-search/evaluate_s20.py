"""Fast S20 dev ablations and exclusive, once-only final sealed evaluation."""
import argparse
import copy
import datetime
import hashlib
import json
import math
import pathlib
import random
import time
import l2_fast
import measure_s9 as s9


def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def dev(profiles, out):
    started = time.perf_counter()
    p = json.loads(profiles.read_text())
    rows = s9.valid(s9.read(s9.HERE/'s9-dataset.jsonl'))
    random.Random(45).shuffle(rows)
    external = s9.valid(s9.read(s9.HERE/'s1-results.jsonl'))
    sets = {'S9-train': rows[:10000], 'holdout': rows[10000:]}
    sets.update({f'S1-{c}': [r for r in external if r['cohort'] == c] for c in 'ABC'})
    result = {}
    predictions = {}
    for mask in range(16):
        p['s20']['switches'] = mask
        score = l2_fast.Score(p)
        pred = {label: [math.log(v) for v in score.score_many([r['members'] for r in rs])] for label, rs in sets.items()}
        result[str(mask)] = {label: s9.metrics(rs, pred[label]) for label, rs in sets.items()}
        predictions[mask] = pred
        score.close()
    # Predeclared main objective: top-100 recall at K5 on S9 holdout, then
    # top-20 K1, then S9 Spearman; S1 metrics are reported as generalization.
    def objective(mask):
        m = result[str(mask)]['holdout']
        return (m['recall']['100']['0.05'], m['recall']['20']['0.01'], m['spearman'], -mask)
    best = max(range(16), key=objective)
    residual = {}
    dev_residual = {}
    rs = sets['holdout']
    for mask in range(16):
        errors = [v-math.log(r['total_damage']) for v, r in zip(predictions[mask]['holdout'], rs)]
        residual[str(mask)] = dict(total_absolute_log_error=sum(abs(v) for v in errors), characters={})
        allrows=sets['S9-train']+rs
        allpred=predictions[mask]['S9-train']+predictions[mask]['holdout']
        allerrors=[v-math.log(r['total_damage']) for v,r in zip(allpred,allrows)]
        dev_residual[str(mask)]=dict(total_absolute_log_error=sum(abs(v) for v in allerrors),characters={})
        for name in p['characters']:
            values = [e for r, e in zip(rs, errors) if name in r['members']]
            residual[str(mask)]['characters'][name] = dict(n=len(values), absolute_log_error=sum(abs(v) for v in values), signed_log_error=sum(values))
            values=[e for r,e in zip(allrows,allerrors) if name in r['members']]
            dev_residual[str(mask)]['characters'][name]=dict(n=len(values),absolute_log_error=sum(abs(v) for v in values),signed_log_error=sum(values))
    save(out/'ablation.json', dict(metrics=result, selected_switches=best,
        objective='S9 holdout top100 K5, then top20 K1, then Spearman, then fewer mask value',
        residual=residual, S9_dev_residual=dev_residual, wall_seconds=time.perf_counter()-started,
        profiles_sha256=hashlib.sha256(profiles.read_bytes()).hexdigest()))
    p['s20']['switches'] = best
    save(out/'final-profiles.json', p)
    print(json.dumps(dict(selected=best, holdout=result[str(best)]['holdout']), ensure_ascii=False))


def final(profiles, previous, sealed, seal, out):
    record = json.loads(seal.read_text())
    actual = hashlib.sha256(sealed.read_bytes()).hexdigest()
    if actual != record['sha256']:
        raise ValueError('Sealed file digest changed')
    event = dict(started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 sealed_sha256=actual, profiles_sha256=hashlib.sha256(profiles.read_bytes()).hexdigest())
    # An exclusive start receipt prevents accidental repeat scoring, including
    # after a failed final coordinator. Development never opens sealed rows.
    with (out/'final-once.json').open('x') as f:
        json.dump(event, f)
    rows = s9.read(sealed)
    valid = [dict(r, total_damage=r['total']) for r in rows if r['status'] == 'ok']
    fitted = json.loads((s9.SCRATCH/'models.json').read_text())['fitted']['M2']
    scores = {}
    for name, path in [('S20 L2', profiles), ('S18 L2', previous)]:
        scorer = l2_fast.Score.load(path)
        scores[name] = s9.metrics(valid, [math.log(v) for v in scorer.score_many([r['members'] for r in valid])])
        scorer.close()
    scores['M0'] = s9.metrics(valid, [math.log(sum(s9.CHARS[n]['potential'] for n in r['members'])) for r in valid])
    scores['M2'] = s9.metrics(valid, [s9.linear_predict(fitted, s9.slot(r['members'])) for r in valid])
    save(out/'final-evaluation.json', dict(metrics=scores, sealed_rows=len(rows), native_successes=len(valid),
        completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), **event))
    print(json.dumps(scores, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['dev', 'final'])
    p.add_argument('--profiles', type=pathlib.Path, required=True)
    p.add_argument('--out', type=pathlib.Path, required=True)
    p.add_argument('--previous', type=pathlib.Path)
    p.add_argument('--sealed', type=pathlib.Path)
    p.add_argument('--seal', type=pathlib.Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.action == 'dev':
        dev(a.profiles, a.out)
    else:
        final(a.profiles, a.previous, a.sealed, a.seal, a.out)
