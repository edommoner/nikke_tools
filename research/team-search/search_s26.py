"""Once-final S26 search; compact lossless artifacts and gx10 detail reuse."""
import argparse
import ctypes as C
import gzip
import itertools
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import truth_s26 as truth


def read(path):
    return json.loads(gzip.decompress(path.read_bytes())) if path.suffix=='.gz' else json.loads(path.read_text())


def save(path,value):
    raw=json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    payload=gzip.compress(raw,mtime=0)
    assert gzip.decompress(payload)==raw
    with path.open('xb') as f:f.write(payload)


def model(out):
    if not (out.parent/'final-evaluation.json').exists():raise RuntimeError('Successful final sealed evaluation required first')
    frozen=read(out.parent/'model-frozen.json');path=Path(frozen['profiles'])
    assert truth.old.digest(path)==frozen['profiles_sha256']
    return read(path)


def enumerate_roster(out,n):
    import l2_fast
    import bench_s23 as b
    b.ISOLATION='S26 coordinator runs no other local scoring/tests during timings; host background activity unverified'
    out.mkdir(exist_ok=True)
    p=model(out)
    frozen=read(out.parent/'model-frozen.json')
    cached=out.parent/f'timings/candidate-1-final-enumerate-{n}.json'
    receipt=out.parent/'timings/candidate-1-final-build.json'
    if cached.exists() and receipt.exists():
        identity=read(receipt)
        if (identity['profiles_sha256']==frozen['profiles_sha256'] and
            identity['library_sha256']==frozen['native_library_sha256'] and
            identity.get('table_sha256')==frozen['table_sha256'] and
            frozen['required_evidence'].get('timings/'+cached.name)==truth.old.digest(cached)):
            result=read(cached)
            result['reuse']=dict(path=str(cached),sha256=truth.old.digest(cached),identity=identity)
            save(out/f'canonical-{n}.json.gz',result)
            print(n,'reused identical final-model enumeration',result['wall_seconds'],flush=True)
            return
    score=l2_fast.Score(p);roster=read(out.parent.parent/f's21/roster-{n}.json')
    before=b.gate(out);start=time.perf_counter()
    result=l2_fast.enumerate_top(score,roster,10000,10,1)
    wall=time.perf_counter()-start;after=b.observation();score.close()
    save(out/f'canonical-{n}.json.gz',dict(before=before,after=after,wall_seconds=wall,**result))
    print(n,wall,result['counts'],flush=True)


def order(out,n):
    import l2_fast
    p=model(out);score=l2_fast.Score(p);source=read(out/f'canonical-{n}.json.gz')['entries']
    rows=[];start=time.perf_counter()
    for offset in range(0,len(source),64):
        batch=source[offset:offset+64]
        orders=[list(s) for r in batch for s in itertools.permutations(r['indices'])]
        values=score.score_indices((C.c_uint32*(len(orders)*5))(*(i for s in orders for i in s)))
        for j,r in enumerate(batch):
            i=min(range(120),key=lambda i:(-values[j*120+i],orders[j*120+i]))
            rows.append(dict(indices=r['indices'],canonical_score=r['score'],
                best=dict(indices=orders[j*120+i],score=values[j*120+i])))
    score.close();rows.sort(key=lambda r:(-r['best']['score'],r['indices']))
    save(out/f'orders-{n}.json.gz',dict(rows=rows,seconds=time.perf_counter()-start,orders_scored=len(source)*120))


def wasm(out,n):
    import bench_s23 as b
    import l2_fast
    model(out)
    b.ISOLATION='S26 coordinator runs no other local scoring/tests during timings; host background activity unverified'
    frozen=read(out.parent/'model-frozen.json')
    table=Path(frozen['table_path'])
    assert truth.old.digest(table)==frozen['table_sha256']
    artifact=Path(frozen['wasm'])
    assert truth.old.digest(artifact)==frozen['wasm_sha256']
    before=b.gate(out);start=time.perf_counter()
    result=b.node_result(['node',str(truth.HERE/'l2_fast/runner.mjs'),'--enumerate',
        '--wasm',str(artifact),'--table',str(table),'--roster',str(out.parent.parent/f's21/roster-{n}.json'),
        '--workers','10','--stride','1','--k','10000'])
    wall=time.perf_counter()-start;after=b.observation()
    native=read(out/f'canonical-{n}.json.gz')
    assert len(result['entries'])==len(native['entries'])==10000
    assert all(a['indices']==c['indices'] and b.struct.pack('<d',a['score'])==b.struct.pack('<d',c['score']) for a,c in zip(result['entries'],native['entries']))
    assert all(result['counts'][k]==native['counts'][k] for k in ('visited','covered','scored'))
    save(out/f'wasm-canonical-{n}.json.gz',dict(before=before,after=after,wall_seconds=wall,
        native_raw_identity=dict(entries=10000,differences=0,counts_identical=True),**result))
    print(n,'WASM',wall,flush=True)


def selection(out):
    p=model(out);names=list(p['characters']);rows=[];lookup={};groups={}
    for n in (206,150):
        ids=[]
        for r in read(out/f'orders-{n}.json.gz')['rows'][:300 if n==206 else 100]:
            squad=tuple(names[i] for i in r['best']['indices'])
            if squad not in lookup:
                lookup[squad]=len(rows);rows.append(dict(id=len(rows),members=list(squad)))
            ids.append(lookup[squad])
        groups[str(n)]=ids
    truth.save(out/'selection.json',dict(rows=rows,groups=groups))
    (out/'bodies.json').symlink_to('../bodies.json')


def reuse(out):
    model(out)
    paths=[truth.HERE/'s21-detailed.jsonl',out.parent.parent/'s22/s21-detailed.jsonl',
           out.parent.parent/'s22/search-cap/s21-detailed.jsonl',out.parent/'s21-detailed.jsonl']
    cache={};hashes={}
    for path in paths:
        hashes[str(path)]=truth.old.digest(path)
        for r in map(json.loads,path.read_text().splitlines()):cache[tuple(r['order'])]=(r,str(path))
    rows=read(out/'selection.json')['rows'];reused=[]
    with (out/'native-journal.jsonl').open('x') as f:
        for row in rows:
            hit=cache.get(tuple(row['members']))
            if hit is None:continue
            r,source=hit
            record=dict(id=row['id'],members=row['members'],total_damage=r['total'],backend=r['backend'],reuse=source)
            if r['status']!='ok':record['error']=r['status']['failed']
            f.write(json.dumps(record,ensure_ascii=False)+'\n')
            reused.append(dict(id=row['id'],source=source,source_id=r['id'],status=r['status']))
    truth.save(out/'reuse.json',dict(requested=len(rows),reused=len(reused),new=len(rows)-len(reused),
        sources=hashes,orders=reused,body_sha256=truth.old.digest(out/'bodies.json')))


def summarize(out):
    model(out)
    rows={r['id']:r for r in map(json.loads,(out/'s21-detailed.jsonl').read_text().splitlines())}
    result={}
    for n,ids in read(out/'selection.json')['groups'].items():
        orders=read(out/f'orders-{n}.json.gz')['rows'][:len(ids)]
        valid=[(rows[i],order) for i,order in zip(ids,orders) if rows[i]['status']=='ok']
        actual=sorted((r for r,o in valid),key=lambda r:(-r['total'],r['id']))
        result[n]=dict(requested=len(ids),successes=len(valid),failures=len(ids)-len(valid),
            max=actual[0]['total'],top10_mean=sum(r['total'] for r in actual[:10])/10,top10=actual[:10],
            **truth.old.metrics([r for r,o in valid],[o['best']['score'] for r,o in valid]))
    truth.save(out/'summary.json',result)
    print(json.dumps({n:{k:v for k,v in r.items() if k!='top10'} for n,r in result.items()}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('enumerate','wasm','order','selection','reuse','summarize'))
    p.add_argument('--out',type=Path,default=truth.DEFAULT/'pipeline')
    p.add_argument('--roster',type=int,choices=(150,206))
    a=p.parse_args()
    import bench_s23 as b
    a.out.mkdir(exist_ok=True)
    command=[sys.executable,'-B',str(b.ROOT/'scripts/nikke_storage.py'),'storage-check',
             '--required-bytes','150000000','--reserve-bytes',str(truth.RESERVE)]
    check=subprocess.run(command,capture_output=True,text=True)
    b.append(a.out/'storage-preflights.jsonl',dict(command=command,exit=check.returncode,stdout=check.stdout))
    if check.returncode:raise RuntimeError('Pipeline storage preflight')
    stop=threading.Event()
    threading.Thread(target=b.monitor,args=(a.out,stop),daemon=True).start()
    try:
        if a.action=='enumerate':enumerate_roster(a.out,a.roster)
        elif a.action in ('order','wasm'):globals()[a.action](a.out,a.roster)
        else:globals()[a.action](a.out)
    finally:stop.set()
