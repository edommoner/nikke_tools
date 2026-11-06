"""Deterministic S20 contexts, paired gx10 runs, and profile construction."""
import argparse
import json
import pathlib
import random
import subprocess
import sys
import measure_s18 as runner

TARGETS = ['티아', '아니스 : 스타', '신데렐라', '홍련 : 신살', '디젤 : 윈터 스위츠']


def prepare(out, previous):
    import measure_s9 as s9
    p = json.loads((previous/'profiles.json').read_text())
    rows = []
    # Reobserve the same contexts to add action-input attribution without
    # changing the S18 primary-context baseline or using truth labels.
    for name, c in p['characters'].items():
        rows.append(dict(id=len(rows), target=name, members=c['standard_squad'], context='primary'))
    excluded = {tuple(r['members']) for f in ('s9-dataset.jsonl', 's1-results.jsonl') for r in s9.read(s9.HERE/f)}
    excluded.update(tuple(s) for c in p['characters'].values() for s in c['standard_squads'])
    rng = random.Random(200206)
    for name in TARGETS:
        for mode in ('single_B1', 'multiple_B1'):
            while True:
                squad = [name, *rng.sample([n for n in s9.NAMES if n != name], 4)]
                stages = [s9.CHARS[n]['burst'] for n in squad]
                if not all(s in stages for s in ('1', '2', '3')):
                    continue
                if (stages.count('1') == 1) != (mode == 'single_B1'):
                    continue
                if tuple(squad) not in excluded:
                    break
            excluded.add(tuple(squad))
            rows.append(dict(id=len(rows), target=name, members=squad, context=mode))
    runner.save(out/'selection.json', dict(seed=200206, selected=rows))
    runner.save(out/'body.json', json.loads((previous/'body.json').read_text()))


def evaluate(body, target, logged):
    r = subprocess.run([sys.executable, '-B', str(runner.b.ROOT/'research/team-search/observe_s20.py')],
        input=json.dumps(dict(body=body, target=target, logged=logged)), text=True,
        capture_output=True, timeout=1800)
    if r.returncode:
        raise RuntimeError(r.stderr[-6000:])
    return json.loads(r.stdout)


def controlled(out, base):
    """One-member or one-priority intervention, with all other slots fixed.

    Donors come from reference effects: Neon full-burst-start crit supply,
    Yuni charge-speed supply. These are diagnosis contexts, chosen without
    ranking labels; they are also the fourth context for the five targets.
    """
    import measure_s9 as s9
    original = json.loads((base/'selection.json').read_text())['selected']
    excluded = {tuple(r['members']) for f in ('s9-dataset.jsonl', 's1-results.jsonl')
                for r in s9.read(s9.HERE/f)}
    excluded.update(tuple(r['members']) for r in original)
    rows = []
    for name in TARGETS:
        control = next(r for r in original if r['target'] == name and r['context'] == 'single_B1')
        members = control['members'][:]
        if name in TARGETS[:2]:
            slot = next(i for i in range(1, 5) if s9.CHARS[members[i]]['burst'] == '3')
            members[slot] = '네온'
            intervention = 'replace one redundant B3 with B1 Neon'
        elif name == '신데렐라':
            members[1] = '유니'
            intervention = 'replace first B2 with charge-speed supplier Yuni'
        elif name == '홍련 : 신살':
            members[3] = '네온'
            intervention = 'replace B1 Misato with crit supplier Neon'
        else:
            members[0], members[2] = members[2], members[0]
            intervention = 'swap target and E.H. burst priority'
        assert len(set(members)) == 5 and s9.s1.covered(members, s9.CHARS)
        assert tuple(members) not in excluded
        excluded.add(tuple(members))
        rows.append(dict(id=216+len(rows), target=name, members=members,
                         context='controlled', control_id=control['id'], intervention=intervention))
    runner.save(out/'selection.json', dict(selected=rows))
    (out/'body.json').write_bytes((base/'body.json').read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'controlled', 'run'])
    parser.add_argument('--out', type=pathlib.Path, required=True)
    parser.add_argument('--previous', type=pathlib.Path)
    parser.add_argument('--workers', type=int, default=20)
    parser.add_argument('--limit', type=int)
    a = parser.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.action == 'prepare':
        prepare(a.out, a.previous)
    elif a.action == 'controlled':
        controlled(a.out, a.previous)
    else:
        if not str(runner.b.ROOT).startswith('/home/'):
            raise RuntimeError('S20 observations are gx10-only')
        runner.evaluate = evaluate
        runner.run(a.out, a.workers, a.limit)
