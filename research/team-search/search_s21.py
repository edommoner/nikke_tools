"""S21 reproducible exhaustive L2 search and bounded evidence coordinator.

All detailed execution is gx10-only. No sealed S20 rows are read.
"""
import argparse, collections, ctypes as C, itertools, json, math, os
from pathlib import Path
import random, shutil, statistics, subprocess, sys, threading, time
HERE=Path(__file__).resolve().parent
DEFAULT=HERE.parents[1].parent/'proofs/claude-product-standard-phase0-v1-20261102/team-search-v1'
SEED=210150
RESERVE=int(20.5*1024**3)

def save(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def read(p):return json.loads(p.read_text())
def profiles(out,mask):
    p=read(out.parent/'s20/dev/final-profiles.json');p['s20']['switches']=mask;return p

def prepare(out):
    from l2_compile import compile_profiles
    out.mkdir(parents=True,exist_ok=True)
    p=profiles(out,15);names=list(p['characters']);assert len(names)==206
    import measure_s9 as s9
    assert set(names)==set(s9.NAMES)
    rosters={150:sorted(random.Random(SEED).sample(range(206),150)),206:list(range(206))}
    save(out/'rosters.json',dict(seed=SEED,rosters=rosters,names=names))
    for n,r in rosters.items():save(out/f'roster-{n}.json',r)
    for mask in (15,2):(out/f'mask-{mask}.l2ft').write_bytes(compile_profiles(profiles(out,mask)))
    save(out/'start.json',dict(time=time.time(),free_bytes=shutil.disk_usage(out).free,budget_bytes=300*1024**2,reserve=RESERVE))
    if shutil.disk_usage(out).free<RESERVE+300*1024**2:raise RuntimeError('storage budget')

def monitor(out,stop):
    samples=[]
    while not stop.is_set():
        free=shutil.disk_usage(out).free;samples.append(dict(time=time.time(),free_bytes=free))
        save(out/f'storage-{os.getpid()}.json',dict(samples=samples,min_free=min(x['free_bytes'] for x in samples)))
        if free<RESERVE:os._exit(3)
        stop.wait(10)

def bench(out):
    import l2_fast
    lib=l2_fast.build();wasm=l2_fast.build(True)
    # Complete native searches first. Remaining configurations explicitly sample
    # one in 100 lexicographic ranks (all first-index partitions participate).
    jobs=[('native',n,15,10,1) for n in (150,206)]
    jobs += [('native',n,2,10,1) for n in (150,206)]
    jobs += [(engine,n,mask,workers,100) for engine in ('native','WASM') for n in (150,206) for mask in (15,2) for workers in (1,10) if not(engine=='native' and workers==10)]
    for engine,n,mask,workers,stride in jobs:
        target=out/f'{engine}-{n}-{mask}-{workers}-{stride}.json'
        if target.exists():continue
        start=time.perf_counter()
        if engine=='native':
            score=l2_fast.Score(profiles(out,mask),library=lib)
            result=l2_fast.enumerate_top(score,read(out/f'roster-{n}.json'),10000,workers,stride);score.close()
        else:
            cmd=['node',str(HERE/'l2_fast/runner.mjs'),'--enumerate','--wasm',str(wasm),'--table',str(out/f'mask-{mask}.l2ft'),'--roster',str(out/f'roster-{n}.json'),'--k','10000','--workers',str(workers),'--stride',str(stride)]
            result=json.loads(subprocess.check_output(cmd,text=True))
        result.update(engine=engine,n=n,mask=mask,workers=workers,stride=stride,wall_seconds=time.perf_counter()-start)
        save(target,result)
        print(target.name,result['counts'],result['wall_seconds'],flush=True)
        with (out/'runs.jsonl').open('a') as f:f.write(json.dumps({k:v for k,v in result.items() if k!='entries'})+'\n')

def order(out):
    import l2_fast
    for n in (150,206):
        for mask in (15,2):
            target=out/f'orders-{n}-{mask}.json'
            if target.exists():continue
            start=time.perf_counter();source=read(out/f'native-{n}-{mask}-10-1.json')['entries'];score=l2_fast.Score(profiles(out,mask));rows=[]
            for offset in range(0,len(source),64):
                batch=source[offset:offset+64];orders=[list(s) for r in batch for s in itertools.permutations(r['indices'])]
                ids=(C.c_uint32*(len(orders)*5))(*(i for s in orders for i in s));values=score.score_indices(ids)
                for j,r in enumerate(batch):
                    candidates=sorted([dict(indices=orders[j*120+i],score=values[j*120+i]) for i in range(120)],key=lambda r:(-r['score'],r['indices']))
                    rows.append(dict(indices=r['indices'],canonical_score=r['score'],best=candidates[0],alternates=candidates[1:3]))
            rows.sort(key=lambda r:(-r['best']['score'],r['indices']));score.close()
            gains=[r['best']['score']/r['canonical_score']-1 for r in rows]
            save(target,dict(rows=rows,seconds=time.perf_counter()-start,orders_scored=len(rows)*120,stats=dict(changed=sum(g>0 for g in gains),median=statistics.median(gains),p90=sorted(gains)[math.ceil(.9*len(gains))-1],maximum=max(gains))))
            print(target.name,read(target)['stats'],flush=True)

def selection(out):
    names=read(out/'rosters.json')['names'];rows=[];lookup={};groups={}
    def add(indices):
        key=tuple(indices)
        if key not in lookup:lookup[key]=len(rows);rows.append(dict(id=len(rows),members=[names[i] for i in indices]))
        return lookup[key]
    for n in (206,150):
        for mask in (15,2):
            rs=read(out/f'orders-{n}-{mask}.json')['rows'][:300 if n==206 else 100]
            groups[f'{n}-{mask}']=[add(r['best']['indices']) for r in rs]
    order_groups=[]
    for r in read(out/'orders-206-15.json')['rows'][:30]:
        order_groups.append(dict(indices=r['indices'],best=add(r['best']['indices']),canonical=add(r['indices']),alternates=[add(a['indices']) for a in r['alternates']]))
    save(out/'selection.json',dict(rows=rows,groups=groups,order_groups=order_groups))
    import measure_s9 as s9
    body=read(Path(s9.INPUT['benchmark']))[0];body.update(s9.INPUT['settings']);save(out/'bodies.json',[body])
    print('detailed unique orders',len(rows),flush=True)

def collect(out):
    import measure_s9 as s9
    if not str(s9.ROOT).startswith('/home/'):raise RuntimeError('gx10-only')
    free=shutil.disk_usage(out).free
    if free<RESERVE+2*1024**3:raise RuntimeError('remote reserve plus 2 GiB peak budget')
    save(out/'collection-storage-start.json',dict(free_bytes=free,reserve=RESERVE,budget_bytes=2*1024**3))
    if (out/'collection.json').exists() and (out/'s21-detailed.jsonl').exists():
        requested=read(out/'selection.json')['rows'];existing=[json.loads(l) for l in (out/'s21-detailed.jsonl').read_text().splitlines()]
        if {r['id']:r['members'] for r in requested}=={r['id']:r['order'] for r in existing}:
            print('Reusing complete identical detailed collection',flush=True);return
        raise RuntimeError('Existing collection identity mismatch')
    s9.SCRATCH=out;s9.INPUT['benchmark']=str(out/'bodies.json');(out/'cache').mkdir(exist_ok=True)
    for name in ('cpp','native'):
        dst=out/'cache'/name
        if not dst.exists():dst.symlink_to(s9.ROOT/'research/portable-build'/name,target_is_directory=True)
    started=time.perf_counter();s9.evaluate(read(out/'selection.json')['rows'],out/'native-journal.jsonl')
    raw=s9.read(out/'native-journal.jsonl');failures=[]
    with (out/'s21-detailed.jsonl').open('w') as f:
        for r in raw:
            ok=r['backend']=='native_detail' and (r.get('total_damage') or 0)>0
            reason=r.get('fallback_reason') or r.get('error') or r.get('unsupported') or 'Missing positive native total'
            status='ok' if ok else dict(failed=reason)
            if not ok:failures.append(dict(id=r['id'],reason=reason))
            f.write(json.dumps(dict(id=r['id'],members=sorted(r['members']),order=r['members'],total=r.get('total_damage'),backend=r['backend'],status=status),ensure_ascii=False,separators=(',',':'))+'\n')
    save(out/'collection.json',dict(wall_seconds=time.perf_counter()-started,rows=len(raw),successes=len(raw)-len(failures),failures=failures,verification='deferred',host=__import__('socket').gethostname()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','bench','order','selection','collect']);p.add_argument('--out',type=Path,default=DEFAULT/'s21');a=p.parse_args()
    stop=threading.Event();thread=threading.Thread(target=monitor,args=(a.out,stop),daemon=True)
    if a.action!='prepare':thread.start()
    try:globals()[a.action](a.out)
    finally:
        stop.set()
        if thread.is_alive():thread.join()
if __name__=='__main__':main()
