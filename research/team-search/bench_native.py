"""Fixed S11 throughput/identity probe; run a fresh interpreter for each code tree.

Only newly created TemporaryDirectory captures are cleaned. Existing evidence and
build caches are never removed. --payloads retains decoded payloads as gzip JSON.
"""
import argparse
import gzip
import json
import os
import shutil
from pathlib import Path
import sys
import tempfile
import time
sys.dont_write_bytecode = True


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--code-root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--assets-root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--count',type=int,default=1024)
    p.add_argument('--shards',type=int,default=1)
    p.add_argument('--shard',type=int,default=0)
    p.add_argument('--threads',type=int,default=10)
    p.add_argument('--repetitions',type=int,default=2)
    p.add_argument('--payloads',action='store_true')
    a=p.parse_args();a.scratch.mkdir(parents=True,exist_ok=True)
    # One bounded batch plus a 20 GiB disk reserve; build caches are warm.
    if shutil.disk_usage(a.scratch).free < 23*1024**3:
        raise RuntimeError('Need 20 GiB reserve plus 3 GiB batch budget')
    root=a.code_root.resolve();assets=a.assets_root.resolve()
    sys.path.insert(0,str(root/'app'))
    import portable_backend as pb,portable_detail as pd,portable_native as pn
    class CacheRoot:
        def __fspath__(self):return str(root)
        def __truediv__(self,part):
            return (assets/part if str(part).startswith('research/portable-build') else root/part)
    pb.ROOT=CacheRoot()
    pn.HOST_THREADS.set(a.threads)
    def forbidden(*args,**kwargs):raise RuntimeError('Benchmark forbids CPU fallback')
    pd._cpu_fallback=forbidden
    pd.cpu_fallback_portable_detail=forbidden
    settings=json.loads((assets/'research/team-search/s1-inputs.json').read_text())
    # Corpus base is the portable copy of the exact S1 benchmark body.
    corpus=json.loads((assets/'research/parity/s1-corpus.json').read_text())
    body=dict(corpus['base']);body.update(settings['settings'])
    rows=[]
    with (assets/'research/team-search/s9-dataset.jsonl').open() as f:
        for line in f:
            row=json.loads(line)
            if row['backend']=='native_detail':rows.append(row)
            if len(rows)==a.count:break
    if len(rows)!=a.count:raise ValueError('Insufficient successful dataset rows')
    rows=rows[a.shard::a.shards]
    reports=[]
    for rep in range(a.repetitions):
        elapsed=0.;checked=0
        payloads=gzip.open(a.scratch/f'payloads-{a.shard}-{rep}.jsonl.gz','wt') if a.payloads else None
        for offset in range(0,len(rows),32):
            batch=rows[offset:offset+32]
            with tempfile.TemporaryDirectory(prefix='bench-capture-',dir=a.scratch) as capture:
                os.environ['NIKKE_DETAIL_CAPTURE_ROOT']=capture
                started=time.perf_counter()
                results=pd.evaluate_many([dict(body,squad=r['members']) for r in batch],verification='deferred')
                elapsed+=time.perf_counter()-started
                for r,result in zip(batch,results,strict=True):
                    value=result.get('result',{})
                    if value.get('compute',{}).get('backend')!='native_detail' or value.get('total_damage')!=r['total_damage']:
                        raise AssertionError(dict(id=r['id'],expected=r['total_damage'],result=result))
                    checked+=1
                    if payloads:payloads.write(json.dumps(dict(id=r['id'],payload=value),ensure_ascii=False)+'\n')
        if payloads:payloads.close()
        report=dict(repetition=rep,rows=checked,seconds=elapsed,ms_per_squad=elapsed*1000/checked,threads=a.threads,shard=a.shard,shards=a.shards,code_root=str(root))
        reports.append(report);print(json.dumps(report),flush=True)
        (a.scratch/f'timings-{a.shard}.json').write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':main()
