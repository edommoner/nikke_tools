"""S26 dev-only v3 residuals and compact paired gx10 observations."""
import argparse
import ast
import collections
import concurrent.futures
import inspect
import gzip
import hashlib
import json
import math
import os
import shutil
from pathlib import Path
import subprocess
import sys
import textwrap
import time
import threading
import truth_s26 as truth


def group_predictions(profiles, squad):
    import l2_score_s22
    method=l2_score_s22.Score.member_scores
    source,start=inspect.getsourcelines(method)
    tree=ast.parse(textwrap.dedent(''.join(source)))
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and ast.unparse(n.target)=='value')
    line=start+node.lineno-1
    groups=[]
    def trace(frame,event,arg):
        if frame.f_code is not method.__code__:return None
        if event=='line' and frame.f_lineno==line:
            v=frame.f_locals;g=v['g']
            unit=g.get('context_unit_s20',g['unit']) if v['switches']&8 else g['unit']
            groups.append(dict(member=v['n'],kind=g['kind'],phase=g['phase'],
                unit=unit,scale=v['scale'],base=v['base'],formed=v['formed'],
                combined=v['combined'],inputs=v['own'],
                predicted=unit*math.prod(v['combined'])*v['scale']))
        return trace
    previous=sys.gettrace();sys.settrace(trace)
    try:members=l2_score_s22.Score(profiles).member_scores(squad)
    finally:sys.settrace(previous)
    return dict(members=members,groups=groups)


def prepare(out):
    import l2_fast
    out.mkdir(exist_ok=False)
    parent=out.parent
    path=truth.HERE/'s26-dev.jsonl'
    assert truth.old.digest(path)==truth.old.previous.read(parent/'seal.json')['files']['dev']['sha256']
    data={r['id']:r for r in map(json.loads,path.read_text().splitlines())}
    best=[data[g['best']] for g in truth.old.previous.read(parent/'selection.json')['groups']
          if g['split']=='dev' and data[g['best']]['status']=='ok']
    profiles=truth.old.previous.read(parent.parent/'s22/final-profiles.json')
    scorer=l2_fast.Score(profiles)
    errors=[(math.log(p/r['total']),r) for p,r in zip(scorer.score_many([r['order'] for r in best]),best)]
    negative=sorted((v for v in errors if v[0]<0),key=lambda v:(v[0],v[1]['id']))
    positive=sorted((v for v in errors if v[0]>=0),key=lambda v:(-v[0],v[1]['id']))
    tails=negative[:50]+positive[:50]
    seen={r['id'] for _,r in tails}
    for item in sorted(errors,key=lambda v:(-abs(v[0]),v[1]['id'])):
        if len(tails)>=100:break
        if item[1]['id'] not in seen:tails.append(item);seen.add(item[1]['id'])
    controls=[v for v in sorted(errors,key=lambda v:(abs(v[0]),v[1]['id'])) if v[1]['id'] not in seen][:50]
    selected=[]
    for error,row in tails+controls:
        pred=group_predictions(profiles,row['order'])
        native=scorer.member_scores(row['order'])
        import struct
        assert all(struct.pack('<d',native[n])==struct.pack('<d',pred['members'][n]) for n in native)
        selected.append(dict(id=row['id'],target=max(native,key=native.get),members=row['order'],
            context='control' if row['id'] not in seen else 'tail',
            log_error=error,truth=row['total'],l2=sum(native.values()),l2_groups=pred))
    scorer.close()
    truth.save(out/'selection.json',dict(selected=selected,rule='largest50 under + largest50 over; fill to100 by absolute error;50 lowest-absolute distinct controls',
        negative_errors=len(negative),nonnegative_errors=len(positive),
        dev_sha256=truth.old.digest(path),profiles_sha256=truth.old.digest(parent.parent/'s22/final-profiles.json')))
    body=truth.old.previous.read(parent/'bodies.json')[0];body['compute_backend']='cpu'
    truth.save(out/'body.json',body)


def run(out,workers):
    import measure_s18 as runner
    import diagnose_s22
    if not str(runner.b.ROOT).startswith('/home/'):raise RuntimeError('gx10 only')
    runner.evaluate=diagnose_s22.evaluate
    rows=truth.old.previous.read(out/'selection.json')['selected']
    (out/'runs').mkdir(exist_ok=True)
    start=time.perf_counter()
    stop=threading.Event()
    def monitor():
        with (out/'storage.jsonl').open('a') as f:
            while not stop.is_set():
                free=shutil.disk_usage(out).free
                f.write(json.dumps(dict(time=truth.now(),free_bytes=free))+'\n');f.flush()
                if free<truth.RESERVE+2*1024**3:os._exit(3)
                stop.wait(5)
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            for result in pool.map(lambda row:runner.one(row,out),rows):
                print(result['selection']['id'],result['wall_seconds'],flush=True)
    finally:stop.set();thread.join()
    truth.save(out/'run.json',dict(workers=workers,squads=len(rows),wall_seconds=time.perf_counter()-start))


def summarize(out, name='diagnosis.json'):
    """Run on gx10; fetch diagnosis.json only, never raw hit observations."""
    import l2_score_s20
    profiles=truth.old.previous.read(out/'profiles.json')
    records=[json.loads(p.read_text()) for p in sorted((out/'runs').glob('*.json'))]
    labels=['hit/event quantity','f1 coefficients','f2 ATK DEF transfer','f3 crit core caps',
            'f4 charge','f5 damage buffs','f6 received damage','f7 element']
    rows=[];aggregates={}
    for r in records:
        assert r['non_interference'] and r['payload_digest']==r['baseline_digest']
        sel=r['selection'];p=r['profile'];pred=sel['l2_groups']
        actual=r['total_damage'];predicted=sum(pred['members'].values())
        error=math.log(predicted/actual)
        weight=error/(predicted-actual) if predicted!=actual else 1./actual
        observed={(g['member'],g['kind'],g['phase']):g for g in p['factor_groups_s22']}
        allocations=collections.Counter();matched_delta=0.;groups=[]
        for g in pred['groups']:
            a=observed.get((g['member'],g['kind'],g['phase']))
            if not a:continue
            values=[g['unit']*g['scale'],*g['combined']]
            tv=[a['prefix_sums'][0],*a['effective_buckets']]
            if any(v is None or v<=0 for v in values+tv):continue
            logs=[math.log(x/y) for x,y in zip(values,tv)];logsum=sum(logs)
            delta=g['predicted']-a['damage'];matched_delta+=delta
            multiplier=delta/logsum if abs(logsum)>1e-12 else a['damage']
            for label,term in zip(labels,logs):allocations[label]+=weight*multiplier*term
            groups.append(dict(member=g['member'],kind=g['kind'],phase=g['phase'],
                predicted=g['predicted'],reference=a['damage'],reference_hits=a['hits'],
                received=a['received'],log_components=dict(zip(labels,logs))))
        allocations['unmatched hits and dependencies']=weight*((predicted-actual)-matched_delta)
        allocations['arithmetic remainder']=error-sum(allocations.values())
        casts,fb,cycles=l2_score_s20.cycle(sel['members'],profiles['characters'],profiles['settings']['duration'])
        actual_casts=collections.Counter(e['character'] for e in p['burst_timeline'] if '사용' in e['event'])
        row=dict(id=sel['id'],context=sel['context'],log_error=error,allocations=dict(allocations),groups=groups,
            members={n:dict(predicted=pred['members'][n],reference=p['member_damage'].get(n,0),
                predicted_casts=casts[n],reference_casts=actual_casts[n]) for n in sel['members']},
            predicted_fb=fb,reference_fb=p['phase_seconds'][1],predicted_cycles=cycles,reference_cycles=p['cycles'],
            native_reference_total_equal=sel['truth']==actual)
        rows.append(row)
        agg=aggregates.setdefault(sel['context'],dict(squads=0,absolute_squad_log_error=0.,absolute_allocations=collections.Counter()))
        agg['squads']+=1;agg['absolute_squad_log_error']+=abs(error)
        for k,v in allocations.items():agg['absolute_allocations'][k]+=abs(v)
    result=dict(squads=len(records),paired_payload_equalities=len(records),
        native_reference_total_equalities=sum(r['native_reference_total_equal'] for r in rows),
        landed_hits=sum(r['profile']['landed_hits'] for r in records),
        baseline_seconds=sum(r['baseline_seconds'] for r in records),
        logged_seconds=sum(r['logged_seconds'] for r in records),aggregates=aggregates,rows=rows,
        note='Ordered algebraic allocation; not independent causal shares. Raw hit evidence remains on gx10.')
    if name=='diagnosis.json':
        # Retain every compact group/factor row losslessly, but transport the
        # detailed summary compressed. The full raw observations stay remote.
        raw=json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
        payload=gzip.compress(raw,mtime=0)
        assert gzip.decompress(payload)==raw
        with (out/'diagnosis-full.json.gz').open('xb') as f:f.write(payload)
        summary={k:v for k,v in result.items() if k!='rows'}
        summary['full_summary']=dict(file='diagnosis-full.json.gz',sha256=hashlib.sha256(payload).hexdigest(),
            uncompressed_sha256=hashlib.sha256(raw).hexdigest(),uncompressed_bytes=len(raw),rows=len(rows),roundtrip_equal=True)
        summary['cycle_comparison']=dict(matches=sum(r['predicted_cycles']==r['reference_cycles'] for r in rows),
            cast_matches=sum(v['predicted_casts']==v['reference_casts'] for r in rows for v in r['members'].values()),
            fb_absolute_mean=sum(abs(r['predicted_fb']-r['reference_fb']) for r in rows)/len(rows),
            fb_absolute_max=max(abs(r['predicted_fb']-r['reference_fb']) for r in rows))
        truth.save(out/name,summary)
    else:truth.save(out/name,result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','run','summarize'))
    p.add_argument('--out',type=Path,default=truth.DEFAULT/'diagnosis')
    p.add_argument('--workers',type=int,default=20)
    p.add_argument('--summary-name',default='diagnosis.json')
    a=p.parse_args()
    if a.action=='run':run(a.out,a.workers)
    elif a.action=='summarize':summarize(a.out,a.summary_name)
    else:globals()[a.action](a.out)
