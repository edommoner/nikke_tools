"""Observation-only repair for standard contexts with no observed personal burst.

No ranking labels are inspected. S9's A-stage coverage rule is weaker than the
reference automatic A->B3 exception. A second fixed context supplies literal
stage 1/2/3 coverage and target-first priority; all evaluated tuples stay excluded.
"""
import argparse, json, pathlib, random
import measure_s9 as s9


def prepare(out):
    selection=json.loads((out/'selection.json').read_text())['selected']
    runs=[json.loads((out/'runs'/f"{row['id']:03}.json").read_text()) for row in selection]
    import engine_worker
    excluded={tuple(r['members']) for name in ('s9-dataset.jsonl','s1-results.jsonl') for r in s9.read(s9.HERE/name)}
    excluded.update(tuple(r['members']) for r in selection)
    rng=random.Random(180207);chosen=[]
    for r in runs:
        row=r['selection'];name=row['target'];stage=str(engine_worker.META[name].get('burst_stage'))
        if r['profile']['casts'] or stage not in ('1','2','3','A'):continue
        while True:
            squad=[name,*rng.sample([n for n in s9.NAMES if n!=name],4)]
            literal={str(engine_worker.META[n].get('burst_stage')) for n in squad if n!='레드 후드'}
            if '레드 후드' in squad:literal.add('3')
            if {'1','2','3'}<=literal and tuple(squad) not in excluded and s9.s1.covered(squad,s9.CHARS):break
        excluded.add(tuple(squad));chosen.append(dict(id=row['id'],target=name,members=squad))
    folder=out/'supplement';folder.mkdir(exist_ok=True)
    (folder/'body.json').write_bytes((out/'body.json').read_bytes())
    (folder/'selection.json').write_text(json.dumps(dict(seed=180207,selected=chosen,reason='no observed personal burst; static literal coverage'),ensure_ascii=False)+'\n')
    print(json.dumps(chosen,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();prepare(a.out)
